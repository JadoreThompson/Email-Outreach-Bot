import asyncio
import os

import aiohttp
from dotenv import load_dotenv

from flask import Blueprint, render_template, request, url_for, flash, redirect, session, jsonify

import psycopg2
from psycopg2 import sql

from db import conn_params

from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
from google.oauth2 import id_token

from functools import wraps  # Decorators

from forms import SignUpForm, LoginForm
from mail import mail_main

from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler


load_dotenv('.env')

views = Blueprint('views', __name__)

# Disabling HTTPs requirement for dev purposes
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

flow = Flow.from_client_secrets_file(
    os.getcwd() + "\static\client_secret_84706046961-bh1h1atvjaim09r3qh1ta1c2v3tefk92.apps.googleusercontent.com.json",
    scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'],
    redirect_uri='http://localhost:5000/callback'
)


running = False


# Email outreach
# Decorator for requiring login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'state' not in session:
            return redirect(url_for('views.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# Running the mail script
scheduler = APScheduler(BackgroundScheduler())
async def main_loop():
    global running
    running = True

    while running:
        try:
            async with aiohttp.ClientSession() as session:
                await mail_main(session)
                print("[MAIL]: Cycle Completed. Waiting before next execution")
        except Exception as e:
            print(f"[SCRIPT ERROR]: ", e)
            await asyncio.sleep(60)


def run_main_outreach():
    asyncio.run(main_loop())


@views.route('/')
def index():
    return render_template('index.html')


@views.route('/signup')
def signup():
    return render_template('signup.html')


@views.route('/signup-user', methods=['POST'])
def signup_user():
    errors = None
    error_message = None
    form = SignUpForm(request.form)

    if form.validate():
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                check_query = sql.SQL('''
                    SELECT email
                    FROM users
                    WHERE email = %s;
                ''')
                cur.execute(check_query, (form.email,))
                row = cur.fetchone()
                if row:
                    error_message = "Email already registered..."
                else:
                    insert_query = sql.SQL('''
                        INSERT INTO users(email, password, firstname)
                        VALUES (%s, %s, %s);
                    ''')
                    cur.execute(insert_query, (form.email, form.confirm, form.name,))

                    flash("Successfully Registered")
                    return redirect(url_for('views.dashboard'))
    else:
        errors = form.errors

    print("Name: ", form.name)
    print("Email: ", form.email)
    print("Password: ", form.password)
    print("Confirm Password: ", form.confirm)
    print("Is validated: ", form.validate())
    print("Form errors: ", form.errors)

    return render_template('signup.html', form=form, errors=errors, error_message=error_message)


@views.route('/login')
def login():
    return render_template('login.html')


@views.route('/login/user', methods=['POST'])
def login_user():
    errors = None
    error_message = None
    form = LoginForm(request.form)

    if form.validate():
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                user_query = sql.SQL("""
                    SELECT email FROM users
                    WHERE email = %s;
                """)
                cur.execute(user_query, (form.email,))
                row = cur.fetchone()
                if row:
                    redirect(url_for('views.dashboard'))
                error_message = "User doesn't exist"
    else:
        errors = form.errors

    print("[FORM ERROR]: ", errors)

    return render_template('login.html', errors=errors,
                           error_message=error_message)


@views.route('/login/google')
def login_google():
    authorisation_url, state = flow.authorization_url()
    print("[AUTH_URL]", authorisation_url)
    session['state'] = state

    print("[AUTH_URL]: ", authorisation_url)
    print("[STATE]: ", state)

    # return render_template('login.html')
    return redirect(authorisation_url)


@views.route('/callback')
def callback():
    try:
        flow.fetch_token(authorization_response=request.url)

        session['state'] = request.args['state']

        credentials = flow.credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, requests.Request(), credentials.client_id)

        print("[ID INFO]: ", id_info)
        session['google_id'] = id_info.get('sub')
        session['name'] = id_info.get('name')
        session['email'] = id_info.get('email')

        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                db_query = sql.SQL("""
                    SELECT email from users
                    WHERE email = %s;
                """)
                cur.execute(db_query, (id_info.get('email'),))
                row = cur.fetchone()
                if row:
                    return redirect(url_for('views.dashboard'))

                insert_script = sql.SQL("""
                    INSERT INTO users (email, password, first_name, google_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """)
                cur.execute(insert_script, (id_info.get('email'), os.getenv('GOOGLE_PLACEHOLDER_PASSWORD'),
                                            id_info.get('name'), id_info.get('sub')), )

        return redirect(url_for('views.dashboard'))

    except Exception as e:
        print("[CALLBACK ERROR]: ", e)
        return "Error processing google login", 500


@views.route('/logout')
@login_required
def logout():
    return


@views.route('/logout/user')
@login_required
def logout_user():
    if session['user_id']:
        session.pop('user_id', None)

    if session['state']:
        session.pop('state', None)

    return redirect(url_for('views.index'))


@views.route('/dashboard')
@login_required
def dashboard():
    print("[DASHBOARD: SESS STATE]: ", session['state'])
    return render_template('dashboard.html')


@views.route('/email-pair', methods=['POST'])
@login_required
def email_pair():
    return


@views.route('/start', methods=['POST'])
def start_outreach():
    global running
    print("[PRIOR OUTREACH BOOL]: ", running)
    if not running:
        scheduler.add_job(id='continuous_outreach', func=run_main_outreach())
        # TODO: create a little green blip showing running
        return jsonify({'message': 'running'})
    else:
        # TODO: process already running
        return jsonify({'message': 'already running'})


@views.route('/stop')
def stop_outreach():
    global running
    if running:
        running = False
        scheduler.remove_job('continuous_outreach')
        # TODO: return the new blip with red showing not running
    else:
        return jsonify({'message': 'No process is currently running'})


@views.route('/notis')
def get_notis():
    return render_template('notis.html')
