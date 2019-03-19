import MySQLdb
from dbFunctions import dbLogIn
from functools import wraps
from flask import current_app
from flask_login import current_user
import logging
import os

errorLog = logging.getLogger("shiftsystem_logger")

class User():
	def __init__(self, colleagueID):
		self.colleagueID = colleagueID
		self.anonymous = False
		self.admin = False

		#check admin database to see if they exist in it...
		adminDB = dbLogIn(database="shiftsystem_admins_devs")
		adminCur = adminDB.cursor()
		adminCur.execute("SELECT * FROM admins WHERE username = %s", (colleagueID,))
		result = adminCur.fetchone()
		if result:
			self.admin = True

		adminCur.close()
		adminDB.close()
		#adminPath = os.path.join(os.path.dirname(__file__), 'admins.txt')
		#with open (adminPath, "r") as Admins:
		#	for line in Admins:
		#		values = line.split(',')
		#		if colleagueID == int(values[4]):
		#			self.admin = True	
		#query database, check if they exist in the database.
		db = dbLogIn(admin = self.admin)
		cur = db.cursor()
		cur.execute("SELECT id, firstName, lastName FROM employeeInfo WHERE username = %s",(colleagueID,))
		result = cur.fetchone()
		if not result: #assuming there is no such user in the db, we log them in as a generic user.
			self.anonymous = True
			self.firstName = "John"
			self.lastName = "Doe"
			self.id = str(3001) # the generic userid
			self.active = False

		else:
			self.id = str(result[0]) #turn into string to ensure that it's returned as a unicode.
			self.firstName = result[1]
			self.lastName = result[2]
			self.active = True
			if int(result[0]) <= 1000: #Admins should be of id 0001, 0002, etc.
				self.admin = True
			elif self.firstName == "Anirudh" or self.id == "1055" or self.id == "1014":
				self.admin = True 

		cur.close() #close the cursor.
		db.close() #close db

	def is_authenticated(self):
		return True

	def is_active(self):
		return self.active
	#Write code to check if user is active.

	def is_anonymous(self):
		return self.anonymous

	def get_id(self):
		return self.id

	def get_username(self):
		return self.username

	def is_admin(self):
		return self.admin

	def load_user(userid):
		db = dbLogIn()
		cur = db.cursor()
		cur.execute("SELECT username FROM employeeInfo WHERE id = %s",(userid,))

		result = cur.fetchone()
		if not result: #if no user with that userid
			return None
		else:
			return User(result[0])
	

def admin_required(func): #A function that ensures that whoever accesses a website is an admin and not a worker.
	errorLog.debug("AdminRequired activated")
	@wraps(func)
	def decorated_view(*args, **kwargs):
		errorLog.debug(str(current_user.id) +  ", is_admin = " + str(current_user.is_admin()))
		if not current_user.is_admin():
			#errorLog.debug(current_user.id +  ", is_admin = " + current_user.is_admin)
			
			return current_app.login_manager.unauthorized()
		return func(*args, **kwargs)
	return decorated_view
