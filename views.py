import os

from flask import Blueprint, render_template, request, url_for, flash, redirect, session
from forms import SignUpForm, LoginForm

import psycopg2
from psycopg2 import sql

from db import conn_params

from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
from google.oauth2 import id_token


views = Blueprint('views', __name__)

# Disabling HTTPs requirement for dev purposes
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
flow = Flow.from_client_secrets_file(
    os.getcwd() + "\static\client_secret_84706046961-bh1h1atvjaim09r3qh1ta1c2v3tefk92.apps.googleusercontent.com.json",
    scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
    redirect_uri='http://localhost:5000/callback'
)
print("[FLOW]: ", flow)

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
                cur.execute(check_query, (form.email, ))
                row = cur.fetchone()
                if row:
                    error_message = "Email already registered..."
                else:
                    insert_query = sql.SQL('''
                        INSERT INTO users(email, password, firstname)
                        VALUES (%s, %s, %s);
                    ''')
                    cur.execute(insert_query, (form.email, form.confirm, form.name, ))

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


@views.route('/login/google')
def login_google():
    authorization_url, state = flow.authorization_url()
    session['state'] = state

    print("[AUTH_URL]: ", authorization_url)
    print("[STATE]: ", state)

    # return render_template('login.html')
    return redirect(authorization_url)


@views.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if 'state' not in session == request.args['state']:
        return 'Invalid state parameter', 400

    credentials = flow.credentials
    id_info = id_token.verify_oauth2_token(
        credentials.id_token, requests.Request(), credentials.client_id)

    session['google_id'] = id_info.get('sub')
    session['name'] = id_info.get('name')
    session['email'] = id_info.get('email')

    return redirect(url_for('views.dashboard'))


@views.route('/login-user', methods=['POST'])
def login_user():
    form = LoginForm()
    pass


@views.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@views.route('/email-pair', methods=['POST'])
def email_pair():
    return


@views.route('/notis')
def get_notis():
    return render_template('notis.html')
