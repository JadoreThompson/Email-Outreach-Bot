from flask import Flask
from views import views


app = Flask(__name__)
app.secret_key = "chicken"
app.register_blueprint(views)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)