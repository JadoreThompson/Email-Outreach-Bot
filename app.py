import os
from dotenv import load_dotenv

from flask import Flask
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from views import views, scheduler


load_dotenv('.env')

# Flask Config
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_APP_SECRET_KEY")
app.register_blueprint(views)

# Scheduler Config
scheduler.init_app(app)
scheduler.start()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
