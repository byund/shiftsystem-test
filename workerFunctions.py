import MySQLdb
from openpyxl import Workbook
from openpyxl import load_workbook
from datetime import date, datetime, timedelta
import daySchedulingFunctions
import AuxiliaryFunctions
import re
import logging
from dbFunctions import dbLogIn, accessDB
import adminFunctions
errorLog = logging.getLogger("shiftsystem_logger")


def checkInEmployee(db, employeeID, actualCheckInTime, shiftID): 
	cursor = db.cursor()	
		
	#build and execute the actual checkin Query
	checkinQuery = ("UPDATE shiftEmployeeLinker SET checkedIn = TRUE, checkinTime = %s "
					"WHERE employeeID = %s AND shiftID = %s")
	subCheckinQuery = ("UPDATE subbedShifts SET checkinTime = %s "
					"WHERE subEmployeeID = %s AND shiftID = %s")
	
	#errorLog.info("Trying to check in worker. Query is : " + checkinQuery + " and data is " + str(actualCheckInTime, employeeID, shiftID))
	try:
		cursor.execute(checkinQuery, (actualCheckInTime, employeeID, shiftID))
		cursor.execute(subCheckinQuery, (actualCheckInTime, employeeID, shiftID))
		cursor.close()
		db.commit()
		errorLog.info("Successfully checked in worker")
		return True
		
	except Exception as e:
		errorLog.debug(cursor._last_executed)
		errorLog.error(e)
		cursor.close()
		db.commit()
		return False



def getCurrentTime(): # Gets the current time and returns it
		
	#TODO- include a check to see if this is a subshift checkin or a normal shift checkin.
	#Figure out how to get location. Perhaps from IP? IN ANY CASE THIS IS A PLACEHOLDER.
	#location = "CMC"
	currentInfo = datetime.today()	#NOTE- This approach means that you checkin based on the server time, not hte javascript time.
	currentDate = currentInfo.strftime("%Y-%m-%d")
	checkinTime = currentInfo.strftime("%H:%M")

	#implement a successcheck..
	return checkinTime


def getCurrentShift(db, location, employeeID): #Given the location and employeeID, finds the shift that a worker is currently in. Allows a worker to check in for a shift up to 10 minutes in advance. Searches through both regularly scheduled shifts and shifts that the employee is picking up as subs. Returns a shiftID.

#TODO- Check in for multiple shifts at once?

	currentInfo = datetime.today()	#NOTE- This approach means that you checkin based on the server time, not the javascript time.
	currentDateTime = currentInfo.strftime("%Y-%m-%d %H:%M")
	cursor = db.cursor()
	#print (currentTime)
	#print (currentDate)
	

	
	shiftQuery = ("""SELECT shiftid FROM shiftEmployeeLinker 
					INNER JOIN ShiftList 
					ON ShiftList.id = shiftEmployeeLinker.shiftid 
					WHERE DATE_SUB(CAST(CONCAT(ShiftList.date, ' ', ShiftList.startTime) as datetime), INTERVAL '10' MINUTE) <= %s AND CAST(CONCAT(ShiftList.endDate, ' ', ShiftList.endTime) as datetime) >= %s AND employeeID = %s 
					UNION 
					SELECT shiftid FROM subbedShifts 
					INNER JOIN ShiftList 
					ON ShiftList.id = subbedShifts.shiftid 
					WHERE DATE_SUB(CAST(CONCAT(ShiftList.date, ' ', ShiftList.startTime) as datetime), INTERVAL '10' MINUTE) <= %s AND CAST(CONCAT(ShiftList.endDate, ' ', ShiftList.endTime) as datetime) >= %s AND subEmployeeID = %s 
					
					ORDER BY shiftid DESC LIMIT 1""")
	
	cursor.execute(shiftQuery, (currentDateTime, currentDateTime, employeeID, currentDateTime, currentDateTime, employeeID))


	#Todo- insert a test table and put in a test so that it actually works.....
	
	#print (location)
	#print (cursor._last_executed)
	result = cursor.fetchone()
	cursor.close()
	#db.close()
	if result:
		shiftID = result[0]
	else:
		shiftID = None

	return shiftID

def getCurrentEmployee(db, username): #Get employeeID given username.
	cursor = db.cursor()
	#print (username)
	cursor.execute("SELECT id from employeeInfo WHERE username = %s", (username,))

	result = cursor.fetchone()
	cursor.close()
	employeeID = result[0]

	return employeeID

def getSubbableShifts(db, employeeID): #Gets all shifts that are in the future that you can sub for. Time is gathered from serverside. Sub requests in the future that conflict with an employees previously scheduled shifts (both regular and other subs that have been picked up) are automatically excluded from the results.
	currentInfo = datetime.today()
	currentDate = currentInfo.strftime("%Y-%m-%d")
	currentTime = currentInfo.strftime("%H:%M")
	currentDateTime = currentInfo.strftime("%Y-%m-%d %H:%M")
	cursor = db.cursor()
	
	#next get all shifts in the future that have an unfulfilled sub request in and (eventually? that are not the employee's own shifts.)
	subQuery = ("""
	SELECT ShiftList.id, DATE_FORMAT(ShiftList.startTime, '%%I:%%i %%p') AS startTime, ShiftList.location, ShiftList.date, ShiftList.day, subRequests.employeeid, employeeInfo.firstName, employeeInfo.lastname
	FROM (
		SELECT shiftEmployeeLinker.shiftID, shiftEmployeeLinker.employeeID, ShiftList.date, ShiftList.startTime FROM shiftEmployeeLinker
		INNER JOIN ShiftList
		ON shiftEmployeeLinker.shiftID = ShiftList.id
		WHERE checkedIn = FALSE 
		AND subRequested = TRUE
		AND subFilled = FALSE) AS subRequests
	LEFT OUTER JOIN (
		SELECT shiftEmployeeLinker.shiftID, ShiftList.date, ShiftList.startTime FROM shiftEmployeeLinker
		INNER JOIN ShiftList
		ON shiftEmployeeLinker.shiftID = ShiftList.id
		WHERE subFilled = FALSE
		AND employeeID = %s) AS employeeShifts
	ON
	CAST(CONCAT(subRequests.date, ' ', subRequests.startTime) AS datetime) = CAST(CONCAT(employeeShifts.date, ' ', employeeShifts.startTime) AS datetime)
	INNER JOIN ShiftList
	ON ShiftList.id = subRequests.shiftID
	INNER JOIN employeeInfo
	ON employeeInfo.id = subRequests.employeeID
	WHERE employeeShifts.shiftID IS NULL
	AND CAST(CONCAT(ShiftList.date, ' ', ShiftList.startTime) AS datetime) > %s
	ORDER BY ShiftList.date ASC, ShiftList.startTime ASC	
	 """)

							
	errorLog.info("Attempting to retrieve all shifts in the future that have an unfulfilled sub request (i.e. are open)")

	try:
		
	#  subQueryData = (currentDate, currentTime, currentDate)
		subQueryData = (employeeID, currentDateTime) 
		#errorLog.debug("Attempting query: " + subQuery + "\n with data: " + str(subQueryData))
		
		cursor.execute(subQuery, subQueryData)
	except Exception as e:
		print (e)
		errorLog.error(e)
		errorLog.debug("Query attempted: " + str(cursor._last_executed))
	
	

	errorLog.info("Successfully retrieved all subbable shifts.")
	subbableShifts = cursor.fetchall()
	#print (employeeID)
	#print (subbableShifts)
	cursor.close()

	errorLog.debug("Subbable Shifts: \n" + str(subbableShifts))

	return subbableShifts
	#Here's a challenge- can you inner join across all three tables to get the employeename in the results as well?



def getSubbingShifts(db, employeeID): #Given an employee, get all shifts that the employee is subbing for in the future, based on server time.
	cursor = db.cursor()

	theNow = datetime.now() #Note: This line means that this method currently gets shifts based on server time.
	currentTime = theNow.strftime("%H:%M")
	currentDate = theNow.strftime("%Y/%m/%d")
	
	#want to get all shifts that user is subbing for in the future.
	subQuery = ("SELECT ShiftList.id, DATE_FORMAT(ShiftList.startTime, '%%I:%%i %%p'), ShiftList.location, DATE_FORMAT(ShiftList.date, '%%m-%%d-%%Y'), ShiftList.day, employeeInfo.id, employeeInfo.firstName, employeeInfo.lastname FROM ShiftList "
						"INNER JOIN subbedShifts "
						"ON ShiftList.id = subbedShifts.shiftID "
						"INNER JOIN employeeInfo "
						"ON subbedShifts.origEmployeeID = employeeInfo.id "
						"WHERE (subbedShifts.subEmployeeID = %s "
						"AND (ShiftList.date = %s AND ShiftList.startTime > %s) )"
						"OR (subbedShifts.subEmployeeID = %s AND ShiftList.date > %s) "
						"AND subbedShifts.checkInTime IS NULL")

	cursor.execute(subQuery, (employeeID, currentDate, currentTime, employeeID, currentDate))
	subbingShifts = cursor.fetchall()

	cursor.close()

	return subbingShifts

def getSubRequestableShifts(db, employeeID): #Get all shifts in the future of a given employee (These are in the future and thus sub requestable)
	currentInfo = datetime.today()
	currentDate = currentInfo.strftime("%Y-%m-%d")
	currentTime = currentInfo.strftime("%H:%M")
	

	cursor = db.cursor()

	#get all possible shifts in the future that the employee can stake using inner join
	subQuery = ("SELECT ShiftList.id, DATE_FORMAT(ShiftList.startTime, '%%I:%%i %%p') AS startTime, ShiftList.location, DATE_FORMAT(ShiftList.date, '%%m-%%d-%%Y'), ShiftList.day, shiftEmployeeLinker.subRequested, shiftEmployeeLinker.subFilled, DATE_FORMAT(shiftEmployeeLinker.subReqTime, '%%m-%%d-%%Y %%I:%%i %%p') FROM ShiftList "
						"INNER JOIN shiftEmployeeLinker "
						"ON ShiftList.id = shiftEmployeeLinker.shiftID "
						"WHERE (shiftEmployeeLinker.employeeID = %s "
						"AND (ShiftList.date = %s AND ShiftList.startTime > %s) AND shiftEmployeeLinker.checkedIn = FALSE)"
						"OR (shiftEmployeeLinker.employeeID = %s AND ShiftList.date > %s AND shiftEmployeeLinker.checkedIn = FALSE)")

	errorLog.info("Retrieving all SubRequestableShifts for employee " + str(employeeID))
	errorLog.debug("Current Date = " + currentDate + ", Current Time = " + currentTime)
	
#	try:
	subQueryData = (employeeID, currentDate, currentTime, employeeID, currentDate)
	  
	  
	errorLog.debug("Attempting query: " + subQuery + "\n with data: " + str(subQueryData))
	  
	cursor.execute(subQuery, subQueryData)
	#except Exception as e:
	#  errorLog.error(e)	  	
	#  errorLog.debug("Query attempted: " + str(cursor._last_executed))
	

	errorLog.info("Successfully retrieved all subRequestable shifts.")
	
	subRequestableShifts = cursor.fetchall()
	cursor.close()
	#errorLog.debug("Sub Requestable Shifts: \n" + str(subRequestableShifts))
	return subRequestableShifts

def checkShiftConflict(db, employeeID, shiftID): #checks if a given shift conflicts with any other shift in an employee's current schedule.
	cur = db.cursor()
	conflictQuery = ("""
	SELECT conflicts.shiftID FROM
		(SELECT ShiftList.id as shiftID, ShiftList.date, ShiftList.startTime
		FROM ShiftList
		WHERE id = %s) AS conflicts
	INNER JOIN
		(
		SELECT * FROM (
			SELECT shiftEmployeeLinker.shiftID as shiftID, ShiftList.date, ShiftList.startTime
			FROM shiftEmployeeLinker
			INNER JOIN ShiftList
			ON ShiftList.id = shiftEmployeeLinker.shiftID
			WHERE shiftEmployeeLinker.employeeID = %s
	
			UNION
		
			SELECT subbedShifts.shiftID as shiftID, ShiftList.date, ShiftList.startTime
			FROM subbedShifts
			INNER JOIN ShiftList
			ON subbedShifts.shiftID = ShiftList.id
			WHERE subbedShifts.subEmployeeID = %s
			) as b 
			
			) as employeeShifts
	ON CAST(CONCAT(employeeShifts.date, ' ', employeeShifts.startTime) AS datetime) = CAST(CONCAT(conflicts.date, ' ', conflicts.startTime) AS datetime)
""")

	cur.execute(conflictQuery, (shiftID, employeeID, employeeID))
	if cur.fetchone(): #if a result exists
		return True
	else:
		return False

def requestSub(db, employeeID, shiftID): #updates a shift for an employee in the shiftEmployeeLinker to mark that the shift has a sub requested.
	cursor = db.cursor()
	theNow = datetime.now() #Gets time of sub request based on server time.
	reqTime = theNow.strftime("%Y-%m-%d %H:%M")
	try:
		subRequest = ("UPDATE shiftEmployeeLinker SET subRequested = TRUE, subReqTime = %s WHERE employeeID = %s and shiftID = %s")
		cursor.execute(subRequest, (reqTime, employeeID, shiftID))
	except Exception as e:
		#log error
		return False
	cursor.close()
	db.commit()
	return True
	


def unrequestSub(db, employeeID, shiftID): #Updates a shift for an employee in the shiftEmployeeLinker to mark that the shift has had a sub request recalled.
	cursor = db.cursor()
	
	try:	
		#Delete the shift from the subbedShifts table if it is in fact filled.
		subUnrequest = ("DELETE FROM subbedShifts WHERE origEmployeeID = %s AND shiftID = %s")
		cursor.execute(subUnrequest, (employeeID, shiftID))
		#Update shiftemployeelinker to reflect that there is no sub request any more for this shift.
		subUnrequest = ("UPDATE shiftEmployeeLinker SET subRequested = FALSE, subReqTime = NULL, subFilled = FALSE WHERE employeeID = %s and shiftID = %s")
		cursor.execute(subUnrequest, (employeeID, shiftID))
		subUnrequest = ("DELETE FROM subbedShifts WHERE origEmployeeID = %s AND shiftID = %s")
		cursor.execute(subUnrequest, (employeeID, shiftID))	
	except Exception as e:
		print (e)
		#log error
		return False
	cursor.close()

	db.commit()
	return True



def getSubStatus(db, shiftID, employeeID): 
	#TODO: Make it so that it passes in username of employee as well.
	
	cursor = db.cursor()
	query = ("SELECT subRequested, subFilled FROM shiftEmployeeLinker WHERE employeeID = %s AND shiftID = %s")
	cursor.execute(query, (employeeID, shiftID))
	result = cursor.fetchone() #of form (subRequested, subFilled)
	#subFilled = result[]
	cursor.close()

	return result



def pickupSub(db, shiftID, origEmployeeID, subEmployeeID):

	cursor = db.cursor()

	
	#check if sub in question has already been filled, or if the request has been rescinded.
	cursor.execute("SELECT subRequested, subFilled from shiftEmployeeLinker "
			"WHERE employeeID = %s AND shiftID = %s", (origEmployeeID, shiftID))

	result = cursor.fetchone()
	subRequested = result[0]
	subFilled = result[1]

	if subRequested == True and subFilled != True:
		#Also double check that the subRequest is actually kosher i.e. the person's current shift schedule has no conflicts.
		
		updateQuery = ("UPDATE shiftEmployeeLinker SET subFilled = TRUE "
						"WHERE employeeID = %s AND shiftID = %s")
		cursor.execute(updateQuery, (origEmployeeID, shiftID))

		insertQuery = ("INSERT INTO subbedShifts (shiftID, origEmployeeID, subEmployeeID)"
						"VALUES (%s, %s, %s)")
		cursor.execute(insertQuery, (shiftID, origEmployeeID, subEmployeeID))

		cursor.close()
		db.commit()




def dropSub(db, shiftID, origEmployeeID, subEmployeeID):

	cursor = db.cursor()
	updateQuery = ("UPDATE shiftEmployeeLinker SET subFilled = FALSE "
					"WHERE employeeID = %s AND shiftID = %s")
	
	cursor.execute(updateQuery, (origEmployeeID, shiftID))

	try:
		delQuery = ("DELETE FROM subbedShifts "
				"WHERE shiftID = %s AND subEmployeeID= %s")
				
		cursor.execute(delQuery, (shiftID, subEmployeeID))

	except:
		print(cursor._last_executed )
	cursor.close()
	db.commit()

def addShiftNotes(db, shiftID, employeeID, notes):
	cur = db.cursor()
	subCMD = ("UPDATE subbedShifts SET notes = %s  WHERE shiftID = %s AND subEmployeeID = %s")
	regCMD = ("UPDATE shiftEmployeeLinker SET notes = %s  WHERE shiftID = %s AND employeeID = %s")

	cur.execute(regCMD, (notes, shiftID, employeeID))
	cur.execute(subCMD, (notes, shiftID, employeeID))

	cur.close()	
	db.commit()

def getShiftNotes(db, shiftID, employeeID): #given a shiftID and employeeID, retrieves the notes for that particular pairing. Sub/non-sub agnostic.
	
	cur = db.cursor()
	notesQuery = """SELECT notes FROM shiftEmployeeLinker 
			WHERE shiftID = %s AND employeeID = %s
			UNION
			SELECT notes from subbedShifts
			WHERE shiftID = %s AND subEmployeeID = %s"""

	cur.execute(notesQuery, (shiftID, employeeID, shiftID, employeeID))
	
	notes = cur.fetchone()

	return notes
def frontEndGetShiftInfo(shiftID, employeeID): #retrieve all data about a particular shift.
	db = dbLogIn()

	shiftInfo = getShiftInfo(db, shiftID, employeeID)

	db.close()

	return shiftInfo

def getShiftInfo(db, shiftID, employeeID): #gets all info about a particular shift and the specified employee covering it.
	subQuery = ("SELECT ShiftList.startTime, ShiftList.location, ShiftList.date, ShiftList.day, employeeinfo.firstName, employeeInfo.lastName, shiftEmployeeLinker.subRequested, shiftEmployeeLinker.subFilled FROM ShiftList "
						"INNER JOIN shiftEmployeeLinker "
						"ON ShiftList.id = shiftEmployeeLinker.shiftID "
						"INNER JOIN employeeInfo "
						"ON shiftEmployeeLinker.employeeID = employeeInfo.id "
						"WHERE (shiftEmployeeLinker.employeeID = %s "
						"AND shiftEmployeeLinker.shiftid = %s)")

	cursor = db.cursor()

	cursor.execute(subQuery, (employeeID, shiftID))

	#print (cursor._last_executed)

	return (cursor.fetchone())

def getShiftCalendarData(db, startDate, endDate): #startDate and endDate should be passed in as ISO8601 Date Strings e.g 2013-12-01
	cur = db.cursor();
	theNow = datetime.now().strftime("%Y-%m-%d %H:%M")
	cur.execute("SELECT id FROM ShiftList where date >= %s AND date <= %s", (startDate, endDate))
	allShiftIDs = cur.fetchall()
	relevantShifts = []
	for elem in allShiftIDs:
		thisShift = {}

		id = str(elem[0]) #Get the actual id out of the tuple...
		shiftInfoDic = accessDB(adminFunctions.getShiftInfo, id) #Result is a dictionary...
		
		thisShift["description"] = (datetime.min + shiftInfoDic["startTime"]).strftime("%I:%M %p") + "-" + (datetime.min + shiftInfoDic["endTime"]).strftime("%I:%M %p") + "\n";
		#convert startTimes and endTimes to strings...
		startTime = (datetime.combine(shiftInfoDic["date"], datetime.min.time()) + shiftInfoDic["startTime"]).strftime("%Y-%m-%dT%H:%M")
		endTime = (datetime.combine(shiftInfoDic["endDate"], datetime.min.time()) + shiftInfoDic["endTime"]).strftime("%Y-%m-%dT%H:%M")
		thisShift["start"] = startTime
		thisShift["end"] = endTime
		
		thisShift["description"] = thisShift["description"] + "Location: " + shiftInfoDic["location"] + "\n"
		
		#next, get all the employeeInfos.
		employeeIDs = shiftInfoDic["employees"]
		title = ""
		for empid in employeeIDs:
			employeeInfo = accessDB(adminFunctions.getEmployeeInfo, empid)
			employeeFirstName = employeeInfo[0]
			employeeName = employeeInfo[0] + " " + employeeInfo[1]
			title = title + employeeFirstName + "\n"
			thisShift["description"] = thisShift["description"] + employeeName + "\n"

		thisShift["title"] = title
		#finally, get location and determine color from that..
		if shiftInfoDic["location"] == "CMC":
			thisShift["color"] = "blue"
		else:
			thisShift["color"] = "#ffa100"
		
		thisShift["id"] = id
		thisShift["location"] = shiftInfoDic["location"]	

		relevantShifts.append(thisShift)

			
	return relevantShifts

def main():
#TODO: FIGURE OUT HOW THIS FLOW SHOULD WORK
#current idea: have every worker login as the same "worker" account, then just deal with checkingin via the names.
	#db = dbLogIn()
	

	#shiftID = getCurrentShift(db, "CMC")

	#print (shiftID)

# #time to test!
	workerNameTuple = ("Anirudh", "Appachar")
# location = "CMC"
# actualcheckinTime = "13:15" #NOTE  You'll need to deal with 24 hour time as well
# date = "2018-03-27"
# checkIn(db, workerNameTuple, actualcheckinTime, location, date)


if __name__ == "__main__":
	main()

