from flask import Blueprint, render_template, request, url_for, flash, redirect
from forms import SignUpForm, LoginForm

import psycopg2
from psycopg2 import sql

from db_connection import conn_params


views = Blueprint('views', __name__)


@views.route('/')
def index():
    return render_template('index.html')


@views.route('/signup')
def signup():
    return render_template('signup.html')


@views.route('/signup-user', methods=['POST'])
def signup_user():
    error = None
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
                    error = "Email already registered..."
                else:
                    insert_query = sql.SQL('''
                        INSERT INTO users(email, password, firstname)
                        VALUES (%s, %s, %s);
                    ''')
                    cur.execute(insert_query, (form.email, form.confirm, form.name, ))
                    flash("Successfully Registered")
                    return redirect(url_for('views.dashboard'))

    return render_template('signup.html', error=error)


@views.route('/login', methods=['POST', 'GET'])
def login():
    return render_template('login.html')


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
