from wtforms import Form, BooleanField, StringField, EmailField, PasswordField, validators


class SignUpForm(Form):
    name = StringField('Name', validators=[validators.length(min=3, max=100)])
    email = EmailField('Email', validators=[validators.Length(min=6, max=255)])
    password = PasswordField('New Password', validators=[
        validators.DataRequired(),
        validators.Length(min=10, max=255),
        validators.EqualTo('confirm', message='Passwords must match!')
    ])
    confirm = PasswordField('Repeat Password')


class LoginForm(Form):
    email = EmailField('Email', validators=[validators.Length(min=6, max=255)])
    password = PasswordField('Password', validators=[
        validators.DataRequired(),
        validators.Length(min=10, max=255)
    ])
