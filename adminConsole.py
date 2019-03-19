from flask import Blueprint, render_template, request, jsonify
from adminFunctions import quickReport, quickWorkerReport,  getAllWorkers, getWorkerInfo, getEmployeeInfo, getShiftInfo,  getCurrentShifts, interleaveShifts, getPastShifts, searchShiftIDs, linkWorkerShift, unlinkWorkerShift
from workerFunctions import getSubRequestableShifts, getSubbingShifts
from datetime import timedelta, datetime
from functools import wraps
from loginFunctions import User, admin_required
from flask_login import (LoginManager, current_user, login_required, login_user, logout_user)
from dbFunctions import dbLogIn, accessDB
import configparser
import os
admin = Blueprint('admin', __name__, template_folder = 'templates')
#stackoverflow.com/questions/38178776/function-object-has-no-attribute-name-when-registering-blueprint
@admin.route('/adminConsole')
@login_required
@admin_required
def adminConsole():
	adminName = current_user.firstName + " " + current_user.lastName

	#Get breakdown of late/missed/on time shifts in past 24 hours...	
	shiftTally = quickReport(timedelta(hours = 24))
	
	#Also get who's currently on shift. This will be done through Javascript (see the method "currentUpcomingShiftInfo()")
	
	return render_template('adminConsole.html', 
				adminName = adminName, 
				total = shiftTally[0], 
				missed = shiftTally[1], 
				fiveMin = shiftTally[2], 
				tenMin = shiftTally[3], 
				fifteenMin = shiftTally[4])


@admin.route('/manageWorkers')
@login_required
@admin_required
def manageWorkers():
	allWorkers = getAllWorkers()
	
	return render_template ('manageWorkers.html', allWorkers = allWorkers)


@admin.route('/workerQuickReport', methods = ['GET'])
@login_required
@admin_required
def workerQuickReport():
	
	#TODO: Make the lower limit for the date into a file that you can just pull the value from.

	lowerDateBound = "2018-04-23"
	upperDateBound = datetime.now().strftime("%Y-%m-%d")	
	if request.args.get('startDate') == None and request.args.get('endDate') == None: #StartDate and EndDate will be sent together no matter what, b/c front end.
		quickWorkerReportTuple = quickWorkerReport(timedelta(hours = 24))
	
		return render_template('quickWorkerReport.html', quickWorkerReportTuple = quickWorkerReportTuple, lowerDateBound = lowerDateBound, upperDateBound = upperDateBound, startDate =None, endDate = None)

	else:
		startDate = request.args.get('startDate')
		endDate = request.args.get('endDate')
		
		quickWorkerReportTuple = quickWorkerReport(timedelta(hours = 24), startDate = startDate, endDate = endDate)
			
		return render_template('quickWorkerReport.html', quickWorkerReportTuple = quickWorkerReportTuple, lowerDateBound = lowerDateBound, upperDateBound = upperDateBound, startDate = startDate, endDate = endDate)

@admin.route('/workerDetails', methods = ['GET', 'POST'])
@login_required
@admin_required
def workerDetails():
	
	workers = getAllWorkers()
	
	#get the specified worker....
	employeeID = request.args.get('workerSelector', None)

	if employeeID != None:
		workerInfoTuple = accessDB(getWorkerInfo, employeeID, isAdmin = True)
		#Tuple is of form (id, firstName, lastName, username, phoneNumber, classYear)
		firstName = workerInfoTuple[1]
		lastName = workerInfoTuple[2]
		username = workerInfoTuple[3]
		phoneNumber = workerInfoTuple[4]
		classYear = workerInfoTuple[5]
		
		#shiftTally = quickReport(timedelta(hours = 24), employeeID = employeeID) 	
		endDate = datetime.now()
		startDate = endDate-timedelta(days=7)
		shiftTally = quickReport(timedelta(hours = 24), employeeID = employeeID, startDate = startDate, endDate = endDate)
		subRequestableShifts = accessDB(getSubRequestableShifts, employeeID, isAdmin=True)
		subbingShifts = accessDB(getSubbingShifts, employeeID, isAdmin = True)
		#print (subbingShifts)	
		upcomingShifts = interleaveShifts(subRequestableShifts, 3, 1, subbingShifts, 3, 1) 

		pastShifts = accessDB(getPastShifts, employeeID, isAdmin = True)
		
		return render_template('workerDetails.html', workers = workers, employeeID = employeeID, firstName = firstName, lastName=lastName, username=username, phoneNumber=phoneNumber, classYear=classYear, total = shiftTally[0], missed = shiftTally[1], fiveMin = shiftTally[2], 
tenMin = shiftTally[3], fifteenMin = shiftTally[4], upcomingShifts = upcomingShifts, pastShifts = pastShifts
)

	else:
		return render_template('workerDetails.html', workers = workers)

@admin.route("/shiftDetails", methods = ['GET'])
@login_required
@admin_required
def shiftDetails():
	shiftID = request.args.get('shiftID', None)
	
	#All shiftDetails will be populated dynamically on the front-end via a Javascript method. See '/getShiftDetails'.	
	return render_template('shiftDetails.html', shiftID=shiftID)


@admin.route('/getShiftDetails', methods=['GET'])
@login_required
@admin_required
def getShiftDetails():
	shiftID = request.args.get("shiftID")
	#print(shiftID)	
	shiftDetails = {}
	id = str(shiftID) #shiftID should be a string.
	shiftInfoDic = accessDB(getShiftInfo, id, isAdmin = True) #Result is a dictionary...
	
	#convert startTimes and endTimes to strings...
	startTime = (datetime.min + shiftInfoDic["startTime"]).strftime("%I:%M %p")
	endTime = (datetime.min + shiftInfoDic["endTime"]).strftime("%I:%M %p")
	date = (shiftInfoDic["date"].strftime("%m-%d-%Y"))
	shiftDetails[id] = {"startTime":startTime, "endTime":endTime, "location":shiftInfoDic["location"], "day":shiftInfoDic["day"], "date":date}
	
	#next, get all the employeeInfos.
	employeeIDs = shiftInfoDic["employees"]
	shiftDetails[id]["employees"] = {}
	for empid in employeeIDs:
		employeeInfo = accessDB(getEmployeeInfo, empid, isAdmin = True)
		employeeName = employeeInfo[0] + " " + employeeInfo[1]
		subEmployeeID = employeeIDs[empid].get("subEmployee", None)
		#if employeeIDs[empid].get("checkinTime") == None:			
		#	checkinTime =  timedelta(seconds=-600) #If the employee hasn't checked in yet, we default to a checkintime of -10 minutes. This is the earliest an employee can checkin and be on time.		
		#else:
		#	checkinTime = employeeIDs[empid].get("checkinTime")
		checkinTime = employeeIDs[empid].get("checkinTime", None)
		if checkinTime != None: #Convert checkinTime into a human-readable string.
			checkinTime = (datetime.min + checkinTime).strftime("%I:%M %p")
		if subEmployeeID != None: #If employee called in a sub.
			subEmployeeInfo = accessDB(getEmployeeInfo, subEmployeeID, isAdmin=True)
			subEmployeeName = subEmployeeInfo[0] + " " + subEmployeeInfo[1]
			
			shiftDetails[id]["employees"][empid]={"name":employeeName, "subEmployee":{"id":subEmployeeID, "name":subEmployeeName,  "checkinTime":checkinTime}  }

		else: #If employee did not call in a sub
			shiftDetails[id]["employees"][empid]={"name":employeeName, "checkinTime":checkinTime}
	return jsonify(shiftDetails)

@admin.route('/updatePieChart', methods = ['GET'])
@login_required
@admin_required
def updatePieChart():
	#We will take in a few parameters first via the query string...

	employeeID = request.args.get('employeeID', None) #gets an employeeID if it is sent.
	
	timeRange = request.args.get('days', 100) #Number of days. Default is 100 days, which is longer than an entire term, and is thus indicative of "all time".
	timeRange = int(timeRange)
	startDate = request.args.get('startDate', None) #For when a custom date is specified.
	endDate = request.args.get('endDate', None)
	
	
	


	if startDate == None and endDate == None: #If no start date is specified, the default behavior is to go from the current day.
		endDate = datetime.now()
		startDate  = endDate - timedelta(days = timeRange)
		
	

	if employeeID == None:
		shiftTally = quickReport(timedelta(hours = 24), startDate = startDate, endDate = endDate)
	
	else:
		shiftTally = quickReport(timedelta(hours = 24), employeeID = employeeID, startDate = startDate, endDate = endDate)
	
	total = shiftTally[0]	
	missed = shiftTally[1]
	fiveMin = shiftTally[2]
	tenMin = shiftTally[3]
	fifteenMin = shiftTally[4]
	
	return (jsonify({"total":total, "missed":missed, "fiveMin":fiveMin, "tenMin":tenMin, "fifteenMin":fifteenMin}))	

@admin.route('/updateCheckinHistory', methods = ['GET'])
@login_required
@admin_required
def updateCheckinHistory():
	#Get parameters...	
	employeeID = request.args.get('employeeID', None) #gets an employeeID if it is sent.
	
	timeRange = request.args.get('days', 100) #Number of days. Default is 100 days, which is longer than an entire term, and is thus indicative of "all time".
	timeRange = int(timeRange)
	startDate = request.args.get('startDate', None) #For when a custom date is specified.
	endDate = request.args.get('endDate', None)

	if startDate == None and endDate == None: #If no start date is specified, the default behavior is to go from the current day.
		endDate = datetime.today()
		
		if timeRange == 100:
			config = configparser.ConfigParser()
			currentDBFile = os.path.join(os.path.dirname(__file__), 'currentDB.ini') #Look up why this path patching is necessary.	
			config.read(currentDBFile)
			startDateStr = config['DBINFO']['dbStart']			
			startDate = datetime.strptime(startDateStr, "%Y-%m-%d")
			

	
		else:
			startDate  = endDate - timedelta(days = timeRange)

	#Results is a set of tuples, each tuple-row is of the form employeeID, shiftID, firstName, lastName, date, startTime, checkinTime
	#now to format them into the dataTable.
	dataTable = {}
	
	#create cols....
	dataTable["cols"] = [{"id":"day", "label":"Day", "type":"date" },
			{"id":"onTime", "label":"onTime", "type":"number" },
			{"id":"missed", "label":"Late", "type":"number" },
			{"id":"fiveMin", "label":"First Five Min", "type":"number" },
			{"id":"tenMin", "label":"First Ten Min", "type":"number" },
			{"id":"fifteenMin", "label":"First Fifteen Min", "type":"number" }
	]
	
	#create rows...
	dataTable["rows"]=[]

	
	#begin populating...
	#FYI-JAVASCRIPT DATE CONSTRUCTOR TAKES MONTHS STARTING AT 0:https://stackoverflow.com/questions/40862362/google-charts-displays-wrong-month
	#SERIOUSLY WHY.
	#WHY.

	while startDate.date() != endDate.date():
		shiftTally = quickReport(timedelta(hours=24), startDate = startDate, endDate = startDate + timedelta(days=1))
		currDateStr = "Date(" + str(startDate.year) + "," + str(startDate.month-1) + "," + str(startDate.day) + ")" #Human readable format: "Date(2010,10,7)"
		dataTable["rows"].append({"c":[{"v":currDateStr},{"v":shiftTally[0]-(shiftTally[1]+shiftTally[2]+shiftTally[3]+shiftTally[4])},{"v":shiftTally[1]},{"v":shiftTally[2]},{"v":shiftTally[3]},{"v":shiftTally[4]}]
					
	
})
		startDate = startDate + timedelta(days=1)				

	return jsonify(dataTable)

@admin.route('/currentUpcomingShiftInfo', methods=['GET'])
@login_required
@admin_required
def currentUpcomingShiftInfo():	
	#TODO: Clean this method up (particularly the str(id) thing, try and work around it so you don't have to change 4 different things each time..
	currentShiftsInfo={}

	#get all current Shifts....
	currentShiftIDs = accessDB(getCurrentShifts, isAdmin=True) #Due to the nature of the db api, ids will be returned in form ((123,),(124,)) as sets of 1-tuples.
	#print(currentShiftIDs)
	for elem in currentShiftIDs:
		id = str(elem[0]) #Get the actual id out of the tuple...
		shiftInfoDic = accessDB(getShiftInfo, id, isAdmin = True) #Result is a dictionary...
		#convert startTimes and endTimes to strings...
		startTime = (datetime.min + shiftInfoDic["startTime"]).strftime("%I:%M %p")
		endTime = (datetime.min + shiftInfoDic["endTime"]).strftime("%I:%M %p")
		currentShiftsInfo[id] = {"startTime":startTime, "endTime":endTime, "location":shiftInfoDic["location"]}

		#next, get all the employeeInfos.
		employeeIDs = shiftInfoDic["employees"]
		currentShiftsInfo[id]["employees"] = {}
		for empid in employeeIDs:
			employeeInfo = accessDB(getEmployeeInfo, empid, isAdmin = True)
			employeeName = employeeInfo[0] + " " + employeeInfo[1]
			subEmployeeID = employeeIDs[empid].get("subEmployee", None)
			if employeeIDs[empid].get("checkinTime") == None:			
				checkinTime =  timedelta(seconds=-600) #If the employee hasn't checked in yet, we default to a checkintime of -10 minutes. This is the earliest an employee can checkin and be on time.		i
				#print(checkinTime)
				#print("TEST")
			else:
				checkinTime = employeeIDs[empid].get("checkinTime")
			if subEmployeeID != None: #If employee called in a sub.
				subEmployeeInfo = accessDB(getEmployeeInfo, subEmployeeID, isAdmin = True)
				subEmployeeName = subEmployeeInfo[0] + " " + subEmployeeInfo[1]
				
				minutesLate = ((checkinTime-shiftInfoDic["startTime"]).seconds)/60
				currentShiftsInfo[id]["employees"][empid]={"name":employeeName, "subEmployee":{"id":subEmployeeID, "name":subEmployeeName,  "minLate":minutesLate}  }

			else: #If employee did not call in a sub
				minutesLate = ((checkinTime-shiftInfoDic["startTime"]).seconds)/60
				currentShiftsInfo[id]["employees"][empid]={"name":employeeName, "minLate":minutesLate}
	
	#print (currentShiftsInfo)
	return jsonify(currentShiftsInfo)

@admin.route('/searchShifts', methods=['POST'])
@login_required
@admin_required
def searchShifts():
	#first, we get all the arguments passed to us...
	id = request.form.get("id", None)
	day = request.form.get("day", None)
	date = request.form.get("date", None)
	startTime = request.form.get("startTime", None)
	endTime = request.form.get("endTime", None)
	location = request.form.get("location", None)
	minDate = request.form.get("minDate", None)
	maxDate = request.form.get("maxDate", None)
	minTime = request.form.get("minTime", None)
	maxTime = request.form.get("maxTime", None)
	#print(day, date, startTime, location)
	shiftIDs = accessDB(searchShiftIDs, isAdmin = True, id=id, day=day, date=date, startTime=startTime, endTime = endTime, location = location, minDate = minDate, maxDate = maxDate, minTime = minTime, maxTime = maxTime)
	#shiftIDs is now a bunch of single tuples...we reformat it...
	searchResults = []
	for elem in shiftIDs:
		searchResults.append(elem[0])
	return jsonify({"shifts":searchResults})

@admin.route('/getAllWorkers', methods=['GET'])
@login_required
@admin_required
def allWorkers():
	workersDict = {}
	allWorkers  = getAllWorkers(); #returns a tuple of tuples of the form (id, firstName, lastName)
	
	for row in allWorkers:
		workersDict[row[0]] = row[1] + " " + row[2]

	return jsonify(workersDict)

@admin.route('/updateShifts', methods=['POST'])
@login_required
@admin_required
def updateShifts():
	#print (request.form)
	shiftID = request.form.get("shiftID")
	allFollowing = request.form.get("allFollowing");
	
	if allFollowing == "false":
		allFollowing = False;
	else:
		allFollowing = True;

	#print (allFollowing)
	prevEmployees = request.form.getlist("prevEmployees[]"); #https://stackoverflow.com/questions/47891935/flask-getlist-always-empty
	selectedEmployees = request.form.getlist("selectedEmployees[]"); #HAHAH USE THIS METHOD HAHAHA
	#First, we want to make the employees into sets.
	prevEmployees = set(prevEmployees);
	selectedEmployees = set(selectedEmployees);
	
	#now we can perform set operations to figure out which workers to add and which workers to remove.
	#The beauty of this is that if there is an intersection, nothing will be done to that worker's records.
	toAdd = selectedEmployees - prevEmployees;
	toRemove = prevEmployees - selectedEmployees;
	if (allFollowing): #If we need to update for multiple shifts..
		#First get the info of the shift in particular...
		shiftDetails = accessDB(getShiftInfo, shiftID, isAdmin = True)

		startTime = shiftDetails.get("startTime") #Note: startTime will be a string here. This is perfectly fine, and in fact rather intended behavior.
		day = shiftDetails.get("day")
		location = shiftDetails.get("location")
		
		#Then get all the subsequent shifts...	
		shiftIDs = accessDB(searchShiftIDs, isAdmin = True, minID=shiftID, day=day, startTime=startTime, location=location) #will be in tuple of tuples...
		for row in shiftIDs:
			shiftID = row[0]
			#Remove the employees who need to be removed.
			for employeeID in toRemove:
				accessDB(unlinkWorkerShift, employeeID, shiftID, isAdmin = True)

			#Add the employees who need to be added.
			for employeeID in toAdd:
				accessDB(linkWorkerShift, employeeID, shiftID, isAdmin = True)


	else: #If you don't need to update for multiple shifts...	
		#Remove the employees who need to be removed.
		for employeeID in toRemove:
			accessDB(unlinkWorkerShift, employeeID, shiftID, isAdmin = True)

		#Add the employees who need to be added.
		for employeeID in toAdd:
			accessDB(linkWorkerShift, employeeID, shiftID, isAdmin = True)

	return ("nothing")


@admin.route('/shiftCalendar', methods = ['GET'])
@login_required
@admin_required
def shiftCalendar():
	return render_template("shiftCalendar.html")
