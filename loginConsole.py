from flask import Flask, Blueprint, render_template, request, redirect
from loginFunctions import User, admin_required
import loginFunctions
from flask_login import (LoginManager, current_user, login_required, login_user, logout_user)
import logging


errorLog = logging.getLogger('shiftsystem_logger')

logins = Blueprint('logins', __name__, template_folder = 'templates')

@logins.route('/')
def welcome():
        if not current_user.is_authenticated:
                return redirect("/login")
        elif int(current_user.id) < 1000:
                return redirect('/adminConsole')
        elif current_user.is_anonymous():
                return redirect("/lostLambOfITS")
        else:
                return redirect("/workerConsole")


@logins.route('/login')
#We're assuming that Shibboleth/SAML (Single Sign On) has already challenged the user to authenticate themselves. Then we can get the authentication information from them if they're accessing the page...
#https://stackoverflow.com/questions/20940651/how-to-access-apache-basic-authentication-user-in-flask
def login():
        authInfo = request.environ
        username = authInfo.get('uid')
        colleagueID = authInfo.get('carlColleagueID')
        user = loginFunctions.User(username)
        #print((username, colleagueID))

        errorLog.debug("Attempting to log " + username + " In.")
        login_user(user)

        errorLog.debug(username + " successfully logged in.")

        #print (os.environ.get("MELLON_uid"))

        #next we check if user is admin or not, and redirect accordingly.
        errorLog.debug(username + " is Admin: " + str(user.is_admin()) )
        if user.is_active() == False:
                return redirect('/lostLambOfITS')
        elif user.is_admin() == False or int(user.id) > 1000:
                return redirect('/workerConsole')
        else:
                return redirect('adminConsole')


@logins.route('/flaskLogout')
@login_required
def logout():
        logout_user()
        return redirect("/mellon/logout?ReturnTo=www.carleton.edu")

@logins.route('/lostLambOfITS')
def lostLamb():
        return render_template('lostLambOfITS.html')
