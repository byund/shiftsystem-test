from flask import Flask, Blueprint, render_template, request, jsonify, Response, redirect, url_for
#from flask_socketio import SocketIO, emit, send
import json
import MySQLdb
from workerFunctions import getCurrentTime, checkInEmployee, getSubRequestableShifts, getSubbableShifts, requestSub, unrequestSub, pickupSub, dropSub, getCurrentShift, getCurrentEmployee, getSubbingShifts, getSubStatus, getShiftCalendarData, addShiftNotes, getShiftNotes, checkShiftConflict
import workerFunctions
from datetime import datetime, timedelta
import queue
import time
from dbFunctions import dbLogIn, accessDB
import loginFunctions
from loginFunctions import User, admin_required
from flask_login import (LoginManager, current_user, login_required, login_user, logout_user)
import os
from adminFunctions import quickReport
from adminConsole import admin
import logging


#app = Flask(__name__)
#app.secret_key = '!\xe1,x?\xcb\xd7\x06f\x1f\x80k\xac\xf4\x08\xe0\xc3\x96\x975\xf5*,?'
#eventStream = queue.Queue()
#app.register_blueprint(admin)

errorLog = logging.getLogger('shiftsystem_logger')

worker = Blueprint('worker', __name__, template_folder = 'templates')


@worker.route('/workerConsole')
@login_required #We call this code only if the user is authenticated and logged in.
def main():
	checkedIn = False
	checkInTime = None
	shiftInfo = None
	shiftNotes = None
	

	db = dbLogIn()
	#when you have an authenticated user, make sure to replace this line with their username.
	
	clientIP = request.environ['REMOTE_ADDR']
	if clientIP == "137.22.5.163" or clientIP == "137.22.29.178" or  clientIP == "137.22.2.38":
		location = "CMC"  #default location
	else:
		location = "ResearchIT"
	#elif clientIP == "137.22.7.132" or clientIP == "137.22.7.136":
		location = "ResearchIT"
	#else:
	#	#not in allowed location for checkin
	#	location = "Unauthorized"
	
	cur = db.cursor()
	employeeID = int(current_user.get_id())
	currentShiftID = getCurrentShift(db, location, employeeID)
	errorLog.info("employeeID: " + str(employeeID) + ", name = " + current_user.firstName + " " + current_user.lastName)
	#TODO -implement check for if there is no employee or shift at this time.
	
	# cur.execute("SELECT checkintime FROM shiftemployeelinker WHERE employeeid = 1001 ORDER BY shiftId DESC LIMIT 1")

	if currentShiftID != None:
		cur.execute("SELECT checkinTime from shiftEmployeeLinker WHERE employeeID = %s AND shiftID = %s UNION SELECT checkinTime from subbedShifts where subEmployeeID = %s AND shiftID = %s", (employeeID, currentShiftID, employeeID, currentShiftID))
		result = cur.fetchone()
		errorLog.debug("Query Executed: " + str(cur._last_executed) + " \n" + "Result: " + str (result)) 
		#print (result) #Investigate why this can sometimes give none but subbingshifts() only ever gives an empty tuple
		if result[0] != None:
			checkedIn = True
			checkInTime = result[0]

		cur.execute("SELECT startTime, location from ShiftList where id = %s", (currentShiftID,))
		shiftInfo = cur.fetchone()
	
	cur.close()

	
	subRequestableShifts = getSubRequestableShifts(db, employeeID)
	#errorLog.debug("Sub Requestable Shifts: " + str(subRequestableShifts))
	
	subbingShifts = getSubbingShifts(db, employeeID)
	#errorLog.debug("Subbing Shifts: " + str(subbingShifts))
	
	upcomingShifts = subRequestableShifts[:5]


	subbableShifts = getSubbableShifts(db, employeeID)
	#errorLog.debug("Subbable Shifts: " + str(subbableShifts))
	
	shiftNotes = getShiftNotes(db, currentShiftID, employeeID)
	if shiftNotes:
		if shiftNotes[0] == "None":
			shiftNotes = None
		else:
			shiftNotes = shiftNotes[0]
	db.close()
	#check if the user is already checked in for this shift.
	
	#will need to implement check for those times when it doesn't even find a result. 
	


	return render_template('workerConsole.html', data = (checkedIn, checkInTime), subRequestableShifts = subRequestableShifts, upcomingShifts = upcomingShifts, subbableShifts = subbableShifts, subbingShifts = subbingShifts, employeeID = employeeID, shiftID = currentShiftID, shiftInfo = shiftInfo, shiftNotes = shiftNotes,  location = location)



@worker.route('/checkin', methods = ['POST'])
def frontEndcheckIn(): 
	#clientIP = request.environ['REMOTE_ADDR']
	#if clientIP != "137.22.5.163" or clientIP != "137.22.29.178" or clientIP != "137.22.2.38" or clientIP != "137.22.7.132" or clientIP != "137.22.7.136":
	#	return jsonify({"Error":"Unauthorized IP"})
	#else:
	#get Employee ID and Shift ID from the POST request
	employeeID = request.form['employeeID']
	shiftID = request.form['shiftID']
	#print ("Hello")
	#print (iemployeeID)
	#print (shiftID)
	
	checkInTime = getCurrentTime()
	accessDB(checkInEmployee, employeeID, checkInTime, shiftID)

	return jsonify({"checkInTime":checkInTime})
	

@worker.route('/requestSub', methods = ['POST'])
@login_required
def frontEndRequestSub():
	
	shiftID = request.form['shiftID']
	employeeID = request.form['employeeID']

	
	if current_user.get_id() != employeeID:
		return jsonify({"Response":"Error: Employee requesting sub is not employee working shift."})

	else:
		accessDB(requestSub, employeeID, shiftID)
		return jsonify({"Response":"Successfully submitted Sub Request."})

@worker.route('/unrequestSub', methods = ['POST'])
@login_required
def frontEndUnrequestSub():
	
	shiftID = request.form['shiftID']
	employeeID = request.form['employeeID']
	
	if current_user.get_id() != employeeID:	
		return jsonify({"Response":"Employee Mismatch"})
	else:	
		accessDB(unrequestSub, employeeID, shiftID)
		return jsonify({"Response":"Success!"})

@worker.route('/pickupSub', methods = ['POST'])
@login_required
def frontEndPickupSub():
	
	origEmployeeID = request.form["origEmployeeID"]
	subEmployeeID = request.form["subEmployeeID"]
	shiftID = request.form["shiftID"]
	
	if current_user.get_id() != subEmployeeID: 
		return jsonify({"Response":"Employee Mismatch" })
	
	else:
		if accessDB(checkShiftConflict, subEmployeeID, shiftID):
			return jsonify({"Response":"Shift Conflicts With Another"})

		else:

			accessDB(pickupSub, shiftID, origEmployeeID, subEmployeeID)

			return jsonify({"Response":"Success!"})

@worker.route('/dropSub', methods = ['POST'])
@login_required
def frontEndDropSub():

		
	origEmployeeID = request.form['origEmployeeID']
	subEmployeeID = request.form['subEmployeeID']	
	shiftID = request.form["shiftID"]


	if current_user.get_id() != subEmployeeID: 
		return jsonify({"Response":"Employee Mismatch"})

	else:
	
	#print (request.form)
	#print (origEmployeeID)
	
	#print (shiftID)
		accessDB(dropSub, shiftID, origEmployeeID, subEmployeeID)

		return jsonify({"Response":"Success!"})



@worker.route('/getSubRequestStatus', methods = ['GET'])
def getSubRequestStatus():
	shiftID = request.args.get('shiftID') #https://stackoverflow.com/questions/10434599/how-to-get-data-received-in-flask-request
	employeeID = request.args.get('employeeID')
	# employeeID = request.form['employeeID']
	# shiftID = request.form['shiftID']
	#print ((employeeID, shiftID))
	
	subStatus = accessDB(getSubStatus, shiftID, employeeID)
	subFilled = subStatus[1]
	subRequested = subStatus[0]

	return (jsonify({"subFilled":subFilled, "subRequested":subRequested}))

@worker.route('/getSubbableShifts', methods = ['GET'])
def frontEndGetSubbableShifts():
	subbableShifts = accessDB(getSubbableShifts)

	shiftInfoList = []
	for elem in subbableShifts:
		shiftID = elem[0]
		origEmployeeID = elem[5]
		diclist = {"shiftID":shiftID, "origEmployeeID":origEmployeeID}
		shiftInfoList.append(diclist)
		#shiftInfoList.update({shiftID : origEmployeeid}) #respectively, shiftid and origemployeeid.
		

	#JSONIFY A LIST. https://stackoverflow.com/questions/12435297/how-do-i-jsonify-a-list-in-flask/35000418#35000418
	#print (shiftInfoList)
	return jsonify(shiftInfoList)

@worker.route('/getSubbingShifts', methods = ['GET']) #Given an employeeID, get all the shifts that they are subbing for.
def frontEndGetSubbingShifts():
	employeeID = request.form['employeeID']

	db = dbLogIn()


	subbingShifts = getSubbingShifts(db, employeeID)

	db.close()

@worker.route('/getSubShiftInfo', methods = ['GET'])
def getSubShiftInfo():
	subbable = True

	shiftID = request.args.get('shiftID') #https://stackoverflow.com/questions/10434599/how-to-get-data-received-in-flask-request
	origEmployeeID = request.args.get('origEmployeeID')

	employeeID = 1006 #this line is a placeholder. Eventually we'll get employeeID from flask-logins.
	
	shiftInfo = workerFunctions.frontEndGetShiftInfo(shiftID, origEmployeeID)
	#print (shiftInfo)
	# time = shiftInfo[0].strftime("%H:%M")
	time = (datetime.min + shiftInfo[0]).time().strftime("%H:%M:%S") #Python retrieves MySQL TIME values as timedeltas, which means you have to add the timedelta interval to a 0:00 time in python to get the actual time. See https://stackoverflow.com/questions/764184/python-how-do-i-get-time-from-a-datetime-timedelta-object for more info.
	location = shiftInfo[1]
	date = str(shiftInfo[2]) #only a string because otherwise javascript will parse it into a full date (which is...nonideal)
	day = shiftInfo[3]
	employeeName = shiftInfo[4] + shiftInfo[5]
	subRequested = shiftInfo[6]
	#print (date)
	if employeeID == origEmployeeID:
		subbable = False

	#BTW You need to rework all the employeeID stuff so that it validates on teh backend, rather than from the frontend.

	return jsonify({"time": time, "location":location, "date":date, "day":day, "subRequested":subRequested, "employeeName":employeeName, "subbable":subbable, "employeeID":employeeID})
	#return ("nothing")

@worker.route('/shiftNotes', methods = ['GET', 'POST'])
@login_required
def shiftNotes():
	employeeID = current_user.get_id()
	
	clientIP = request.environ['REMOTE_ADDR']
	if clientIP == "137.22.5.163" or clientIP == "137.22.29.178" or  clientIP == "137.22.2.38":
		location = "CMC"  #default location
	else:
		location = "ResearchIT"
	#elif clientIP == "137.22.7.132" or clientIP == "137.22.7.136":
	#	location = "ResearchIT"
	#else:
	#	#not in allowed location for checkin
	#	location = "Unauthorized"
	
	shiftID = accessDB(getCurrentShift, location, employeeID) 

	if request.method == 'POST':	
		note = request.form.get("note_input");
		#truncate note to 255 characters, just in case some joker tries to game the system.
		note = note[:255]
	
		accessDB(addShiftNotes, shiftID, employeeID, note)	
		return ("nothing")
	
	elif request.method == 'GET':
	#retrieve the note for the shift already.
		notes = accessDB(getShiftNotes, shiftID, employeeID)		
		if notes: #if notes isn't empty...
			return jsonify({"notes": notes[0]}) #it's a tuple b/c it's a result set, so we need to extract the content from the tuple. 
		else:
			return jsonify({"noContent"})


@worker.route('/shiftCalendarData', methods = ['GET'])
def shiftCalendarData():
	startDate = request.args.get("start")
	endDate = request.args.get("end")

	relevantShifts = accessDB(getShiftCalendarData, startDate, endDate)
	
	return jsonify(relevantShifts)
	

if __name__ == '__main__':
	socketio.run(app)
