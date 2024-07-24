import os
from dotenv import load_dotenv

from flask import Flask
from views import views


load_dotenv('.env')

# Flask Config
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_APP_SECRET_KEY")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
