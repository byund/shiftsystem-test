from flask import Flask
from flask_login import (LoginManager, current_user)
from loginFunctions import User
import logging
from adminConsole import admin
from workerConsole import worker
from loginConsole import logins
app = Flask(__name__)
app.secret_key = '!\xe1,x?\xcb\xd7\x06f\x1f\x80k\xac\xf4\x08\xe0\xc3\x96\x975\xf5*,?'
app.config['TEMPLATES_AUTO_RELOAD'] = True #This should fix some caching issues we see when templating the workerConsole.
#eventStream = queue.Queue()
app.register_blueprint(admin)
app.register_blueprint(worker)
app.register_blueprint(logins)
errorLog = logging.getLogger('shiftsystem_logger')

login_manager = LoginManager()
login_manager.login_view = "/"

@login_manager.user_loader
def load_user(user_id):
	return User.load_user(user_id)

login_manager.init_app(app)
