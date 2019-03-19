# a file that takes care of all the functions that an administrator would need to do.
import MySQLdb
from datetime import timedelta, datetime
from dbFunctions import dbLogIn, accessDB
import reportFunctions
import logging

errorLog = logging.getLogger('shiftsystem_logger')



def addWorker(firstName, lastName):
	db = dbLogIn()
	cur = db.cursor()
	
	insertCmd = "INSERT INTO employeeInfo (firstName, lastName) "
	"VALUES (%s, %s)"
	
	try:
		cursor.execute(insertCMD, (firstName, lastName))
		cursor.close()
		db.commit()
		db.close()
		return True
	except Exception as e:
		#print (e)
		cursor.close()
		db.close()
		return False

def removeWorker(firstName, lastName):
	db = dbLogIn()
	cur = db.cursor()
	delCmd = "DELETE FROM employeeInfo "
	"WHERE firstName = %s and lastName = %s"
	try:
		cur.execute(delCmd, (firstName, lastName))
		db.commit()
		cursor.close()
		db.close()
	except Exception as e:
		#print (e)
		cursor.close()
		db.close()
		return False

def linkWorkerShift(db, employeeID, shiftID): #Given a shiftID and employeeID, assigns the employee to the shift. This will check if there are any pre-existing schedule conflicts for the worker (Subbing Shifts that conflict will automatically get removed). If there aren't, the shift gets added. Otherwise, it returns an error with the conflicting shiftIDs.
	cur = db.cursor()
	
	#First, we check for conflicts for that employee with a shift.
	conflictQuery =  (
	"""SELECT scheduled.shiftID FROM
		(SELECT shiftID, ShiftList.startTime, ShiftList.date FROM
			shiftEmployeeLinker
			INNER JOIN ShiftList
			ON shiftEmployeeLinker.shiftID = ShiftList.id
			WHERE employeeID = %s) as scheduled
		INNER JOIN
		(SELECT id as shiftID, startTime, date
			FROM ShiftList
			WHERE id = %s) as new
		ON scheduled.shiftID = new.shiftID
		WHERE scheduled.date = new.date
		AND scheduled.startTime = new.startTime
	""")
	
	cur.execute(conflictQuery, (employeeID, shiftID))
	conflictIDs = cur.fetchall()
	
	if conflictIDs: #if there are conflicts...
		return {"error":conflictIDs}
	else:
		#find all subbing shifts which conflict with new shift...
						
		subConflictQuery =  (
		"""SELECT subbing.shiftID FROM
			(SELECT shiftID, ShiftList.startTime, ShiftList.date FROM
				subbedShifts
				INNER JOIN ShiftList
				ON subbedShifts.shiftID = ShiftList.id
				WHERE subEmployeeID = %s) as subbing
			INNER JOIN
			(SELECT id as shiftID, startTime, date
				FROM ShiftList
				WHERE id = %s) as new
			ON subbing.shiftID = new.shiftID
			WHERE subbing.date = new.date
			AND subbing.startTime = new.startTime
		""")
		cur.execute(subConflictQuery, (employeeID, shiftID))
		subConflictIDs = cur.fetchall()
		#REMOVE ALL SUB CONFLICTS
		#NOTE: also worth a try....the command "DELETE FROM subbedShifts where shiftID in %s AND employeeID = %s", with input (subConflictIDs, employeeID). subConflictIDs must be a tuple.
		#ALSO WORTH A TRY: Skip the comparison direclty and just do:
		#"DELETE FROM subbedShifts where employeeID = %s and shiftID in ""INSERT SUBCONFLICT QUERY HERE"
		for id in subConflictIDs:
			cur.execute("DELETE FROM subbedShifts WHERE shiftID = %s AND subEmployeeID = %s", (id, employeeID))
		try:
			cur.execute("INSERT INTO shiftEmployeeLinker (employeeID, shiftID) VALUES (%s, %s)", (employeeID, shiftID))
			
			db.commit()
			cur.close()
			return True
		except Exception as e:
		
			cur.close()
			return False


	
def unlinkWorkerShift(db, employeeID, shiftID): #Given an employeeID and a shiftID, unassigns the worker from the shift.
	cur = db.cursor()
	
	try:
		cur.execute("DELETE FROM shiftEmployeeLinker WHERE employeeID = %s AND shiftID = %s", (employeeID, shiftID))

		db.commit()
		cur.close()
		return True
	except Exception as e:
		
		cur.close()
		return False

def swapWorkerShifts(db, employeeID, oldShiftID, newShiftID):
#will switch worker assignments for shifts. Due to the way this funcitons, I think it's best to log in once with whatever function calls this.
	
	unlink = unlinkWorkerShift(db, employeeID, oldShiftID)
	link = linkWorkerShift(db, employeeID, newShiftID)

def quickReport(timeRange, **kwargs): #A function that reports the breakdown of shift checkins overall, over a given timerange, up to the present time. Includes both subbedShifts and regularShifts.
#You may specify an individual worker, by employeeID
#You may specify a startDate and an endDate. Doing so overrides the timerange parameter and goes from 00:00 on the startDate to 23:59 on the endDate.
	
	#get employeeID if there is one.
	employeeID = kwargs.get("employeeID", None)
	
	#get relevant start and end datetimes based on given time range. 
	theNow = datetime.now()
	theYesterday = theNow - timeRange #timeRange must be a timedelta object.
	currDateTime = theNow.strftime("%Y/%m/%d %H:%M")
	yesterDateTime = theYesterday.strftime("%Y/%m/%d %H:%M")

	#get startDate and endDate if specified. If not, defaults to the previously defined timeranges.
	startDate = kwargs.get("startDate", theYesterday)
	endDate = kwargs.get("endDate", currDateTime)
		
	if employeeID == None:

		report = reportFunctions.quickReport(startDate, endDate)
	else:
		report = accessDB(reportFunctions.quickWorkerSummary, startDate, endDate, employeeID)	
	#print (report)

	#bin the shifts. Indices 5 and 6 are the shift's startTime and checkinTime.	
	binnedShifts = shiftBinner(report, 5, 6)
	
	#extract the counts and assign to human-readable variables.
	missed = len(binnedShifts[4])
	fiveMin = len(binnedShifts[1])
	tenMin = len(binnedShifts[2])
	fifteenMin = len(binnedShifts[3])


	return (len(report), missed, fiveMin, tenMin, fifteenMin)



def quickWorkerReport(timeRange, **kwargs): #A function that reports the breakdown of shift checkins per worker, for all workers, in a given timerange.
#Default behavior is to get data across a timeRange up until the present day, AND present time. For example, firing this at 1:30PM on Friday with a timerange of 24 hours will get data starting from Thursday at 1:30PM.
#You may override this by providing "startDate" and "endDate" keyword arguments. In this case, unless these parameters have Hour and Minute information, the default will be from 00:00 on the startDate to 23:59 on the endDate.

	workerDict = {}
	
	theNow = datetime.now()
	theYesterday = theNow - timeRange #timeRange must be a timedelta object.

	currDateTime = theNow.strftime("%Y/%m/%d %H:%M")
	yesterDateTime = theYesterday.strftime("%Y/%m/%d %H:%M")
	#currTime = theNow.strftime("%H:%M")

	#Get a startDate and endDate if specified.	
	startDate = kwargs.get("startDate", theYesterday)
	endDate = kwargs.get("endDate", currDateTime)
	
	report = reportFunctions.quickReport(startDate, endDate)
	#having gotten all the shifts, we can now begin binning.
	for row in report:
		#First, extract employeeInfo.
		employeeID = row[0]
		employeeName = row[2] + " " + row[3]
		if employeeID not in workerDict: #if the employeeID is not in the dictionary...
			workerDict[employeeID] = [employeeName, 0, 0, 0, 0, 0]
			#here, the list refers to the following bins: early, 5min, 10min, 15min, missed.
		
		#Now that the employee is in the dict, we bin according to the timeLate.

		if row[6] == None:#If no checkintime..
			workerDict[employeeID][5] += 1
		else:	
		
			timeLate = row[6] - row[5]
			
			if (timeLate > timedelta(minutes = 0)) and (timeLate <= timedelta(minutes = 5)):
				workerDict[employeeID][2] += 1
			
			elif (timeLate > timedelta(minutes = 5)) and (timeLate <= timedelta(minutes = 10)):
				workerDict[employeeID][3] += 1
		
			elif (timeLate > timedelta(minutes = 10)) and (timeLate <= timedelta(minutes = 15)):
				workerDict[employeeID][4] += 1

			elif (timeLate > timedelta(minutes = 15)):
				workerDict[employeeID][5] += 1

			else: #if none of these bins work, the worker must have been an early checkin.
				workerDict[employeeID][1] += 1

	
	
	#having binned everything, we now turn the workerDict into tuples that we can return to the calling function.
	tempList = []
	for employeeID in workerDict:
		tempList.append(tuple(workerDict[employeeID]))

	quickWorkerReportTuple = tuple(tempList)

	return quickWorkerReportTuple
	
			

def getAllWorkers(): #Gets id, firstName and lastName of all workers (intentionally excludes admins)
	db = dbLogIn()
	cur = db.cursor()
	errorLog.info("Attempting to fetch all workers...")
	errorLog.debug("Attempting Query: SELECT id, firstName, lastName FROM employeeInfo WHERE id >= 1000")
	cur.execute("SELECT id, firstName, lastName FROM employeeInfo WHERE id >= 1000")
	

	workers = cur.fetchall()
	errorLog.info("Succesfully fetched all workers.")

	cur.close()
	db.close()
	return workers


def getWorkerInfo(db, employeeID): #Get all info for a given worker from the database.
#Resulting tuple is of form (id, firstName, lastName, username, phoneNumber, classYear)
	cur = db.cursor()
	
	errorLog.info("Fetching info for employee with id " + employeeID)
	errorLog.debug("Attempting Query: SELECT * from employeeInfo where id = " + employeeID)
	cur.execute("SELECT id, firstName, lastName, username, phoneNumber, classYear from employeeInfo where id = %s", (employeeID,))
	workerInfo = cur.fetchone()
	cur.close()
	
	return workerInfo

def getCurrentShifts(db): #Given the current time, finds the shift(s) that are happening. Returns corresponding shiftIDs.
#ShiftIDS will be returned as the rows that the cursor fetches, i.e ((shiftID1,), (shiftID2,.....))

	currentInfo = datetime.today()	#NOTE- This approach means that you are getting shiftData based on serverside time.
	currentDateTime = currentInfo.strftime("%Y-%m-%d %H:%M")
	
	cursor = db.cursor()
	

	#Get shift info. This query will search for the shift that is happening at the current time in both the libe and the CMC.

	shiftQuery = ("SELECT id from ShiftList WHERE "
			"CAST(CONCAT(date, ' ', startTime) AS datetime) <= %s "
			"AND CAST(CONCAT(endDate, ' ', endTime) AS datetime) >= %s") 
			

	
	
	cursor.execute(shiftQuery, (currentDateTime, currentDateTime))

	
	#print (location)
	#print (cursor._last_executed)
	shiftIDs = cursor.fetchall()
	cursor.close()
	
	
	return shiftIDs

def getPastShifts(db, employeeID): #Gets ALL past shifts for an employee, including sub requests that were filled and sub requests that the employee picked up.
#Results are returned as the rows that the cursor originally fetched, i.e a tuple of tuples.
#Individual rows are tuples of the form (shiftID, isSub, Location, Day, date, startTime, checkinTime, notes, subRequested, subFilled)

	cur = db.cursor()
	theNow = datetime.now()
	currentDateTime = theNow.strftime("%Y-%m-%d %H:%M")	
	query = ("""
	(SELECT shiftEmployeeLinker.shiftID, NULL as isSub, ShiftList.location, ShiftList.day, DATE_FORMAT(ShiftList.date, '%%m-%%d-%%Y'), DATE_FORMAT(ShiftList.startTime, '%%I:%%i %%p'), DATE_FORMAT(shiftEmployeeLinker.checkinTime, '%%I:%%i %%p') as actualCheckIn, shiftEmployeeLinker.notes, shiftEmployeeLinker.subRequested, shiftEmployeeLinker.subFilled
	FROM shiftEmployeeLinker
	INNER JOIN ShiftList
	ON shiftEmployeeLinker.shiftID = ShiftList.id
	WHERE shiftEmployeeLinker.employeeID = %s AND CAST(CONCAT(ShiftList.date, ' ', ShiftList.startTime) AS datetime) < %s)
	
	UNION

	(SELECT subbedShifts.shiftID, True as isSub, ShiftList.location, ShiftList.day, ShiftList.date, DATE_FORMAT(ShiftList.startTime, '%%I:%%i %%p'), DATE_FORMAT(subbedShifts.checkinTime, '%%I:%%i %%p') as actualCheckIn, subbedShifts.notes, NULL as dummy1, NULL as dummy2
	FROM subbedShifts
	INNER JOIN ShiftList
	ON subbedShifts.shiftID = ShiftList.id
	WHERE subbedShifts.subEmployeeID = %s AND CAST(CONCAT(ShiftList.date, ' ', ShiftList.startTime) AS datetime) < %s)
	
	ORDER BY shiftID ASC	
	""")

	cur.execute(query, (employeeID, currentDateTime, employeeID, currentDateTime))
	
	pastShifts = cur.fetchall()
	
	return pastShifts


def interleaveShifts(shiftTuple1, d1, t1, shiftTuple2, d2, t2): #A method for combining different result sets of shifts. Given two ordered sets and the indices corresponding to their date and time values, this method merges the two in order.
#This method assumes that each result set is individually ordered by date/time in ascending order.
 
	shiftList = []
	x = 0	#to track our position in the first shiftTuple
	y = 0	#to track our position in the second shiftTuple

	while x <= (len(shiftTuple1) -1) and y <= (len(shiftTuple2)-1):
		shiftDate1 = datetime.strptime(str(shiftTuple1[x][d1] + " " + shiftTuple1[x][t1]), "%m-%d-%Y %I:%M %p" )
		shiftDate2 = datetime.strptime(str(shiftTuple2[y][d2] + " " + shiftTuple1[y][t2]), "%m-%d-%Y %I:%M %p" )
		
		if shiftDate1 <= shiftDate2:
			shiftList.append(shiftTuple1[x])
			x += 1
		else:
			shiftList.append(shiftTuple2[y])
			y += 1

		
	#once you've broken out of the loop, just add the rest of whichever tuple has more elements.

	if x == (len(shiftTuple1)):
		for elem in shiftTuple2[y:]:
			shiftList.append(elem)
	
	elif y == (len(shiftTuple2)):
		for elem in shiftTuple1[x:]:
			shiftList.append(elem)

	#convert resulting list into tuple and return.

	return tuple(shiftList)

	
		
def getShiftInfo(db, shiftID): #gets start time, end time, day, date,  location, and all the employees who are supposed to be working that shift.
#Result is a dictionary of the form:
#{
#	"startTime":
#	"endTime":
#	"day":
#	"date":
#	"endDate":
#	"location":
#	"employees":{
#		"employeeID":{
#			"subEmployeeID": //Only shows up if the employee called in a sub and the sub was picked up.
#			"checkinTime":	//Referes to employee's check in time unless a sub exists, at which point it refers to the checkinTime of the sub.
#				}
#			
#		
#			}
#
#
#}


	cur = db.cursor()
	
	shiftInfoDic={}	
	cur.execute("SELECT startTime, endTime, day, date, endDate, location FROM ShiftList WHERE id = %s",(shiftID,))
	result = cur.fetchone();
	shiftInfoDic["startTime"] = result[0]
	shiftInfoDic["endTime"] = result[1]
	shiftInfoDic["day"] = result[2]
	shiftInfoDic["date"] = result[3]
	shiftInfoDic["endDate"] = result[4]
	shiftInfoDic["location"] = result[5]
	
	#next we get the employeeIDs...including substitutes.
	shiftInfoDic["employees"] = {}
	cur.execute("Select employeeID, subFilled, checkinTime from shiftEmployeeLinker where shiftID = %s", (shiftID,))
	result = cur.fetchall()
	for row in result:
		employeeID = row[0]
		if row[1] == False: #if the employee has not had a filled sub request.
			shiftInfoDic["employees"][employeeID] = {"checkinTime":row[2]} #fill in with checkintime.
		else: #if the employee does have a filled subrequest
			cur.execute("Select subEmployeeID, checkinTime from subbedShifts where shiftID = %s AND origEmployeeID = %s", (shiftID, employeeID))
			subResult = cur.fetchone()
			subEmployeeID = subResult[0]
			shiftInfoDic["employees"][employeeID] = { "subEmployee":subEmployeeID, "checkinTime":subResult[1]}	
	

	cur.close()
	
	return shiftInfoDic
	
def getEmployeeInfo(db, employeeID):
	cur = db.cursor()
	cur.execute("SELECT firstName, lastName FROM employeeInfo where id = %s",(employeeID,))	
	result = cur.fetchone()
	cur.close()
	return result	
	

def shiftBinner(shifts, checkinTimeIndex, actualCheckinTimeIndex): #Takes a tuple of shift tuples, and arguments specifying which indices of the tuple correspond to the start of the shift and the actual time checked in. Bins shifts into early, 5 minutes, 10 minutes, 15 minutes, and missed. Returns a tuple of lists, each list represents a bin.
	early = []
	fiveMin = []
	tenMin = []
	fifteenMin = []
	missed = []

	for shift in shifts:
		#check if employee actually checked in...
		if shift[actualCheckinTimeIndex] == None:
			missed.append(shift)
		else:
			timeLate = shift[actualCheckinTimeIndex] - shift[checkinTimeIndex]

			if (timeLate > timedelta(minutes = 0)) and (timeLate <= timedelta(minutes = 5)): #Worker checked in in first five minutes
					fiveMin.append(shift)

			elif (timeLate > timedelta(minutes = 5)) and (timeLate <= timedelta(minutes = 10)):
					tenMin.append(shift)

			elif (timeLate > timedelta(minutes = 10)) and (timeLate <= timedelta(minutes = 15)):
					fifteenMin.append(shift)

			elif (timeLate > timedelta(minutes = 15)):
					missed.append(shift)

			else: #if none of these bins work, the worker must have been an early checkin.
					early.append(shift)


	return (early, fiveMin, tenMin, fifteenMin, missed)	


def searchShiftIDs(db, **kwargs):#A function to construct a sql query dynamically that will search for shifts at the specified time/date/date range/etc. Returns shiftIDS.
	
	#First, construct the base cmd and the base list of parameters.
	
	query = "SELECT id from ShiftList WHERE 1 = 1 " #The 1=1 part allows us to string on as many "ANDs" as we like, thus dynamically building the query.
	parameters = []

	if kwargs.get("id", None):
		query = query +  "AND id = %s "
		parameters.append(kwargs["id"])

	if kwargs.get("minID", None):
		query = query + "AND id >= %s "
		parameters.append(kwargs["minID"])

	if kwargs.get("startTime", None):
		query = query + "AND startTime = %s "
		parameters.append(kwargs["startTime"])

	if kwargs.get("endTime", None):
		query = query + "AND endTime = %s "
		parameters.append(kwargs["endTime"])

	if kwargs.get("location", None):
		query = query +  "AND location = %s "
		parameters.append(kwargs["location"])
		
	if kwargs.get("date", None): #dates and times should be passed in directly formatted in yyyy/mm/dd and hh:mm respectively.
		query = query + "AND date = %s "
		parameters.append(kwargs["date"])
	
	if kwargs.get("day", None):
		query = query + "AND day = %s "
		parameters.append(kwargs["day"])

	if kwargs.get("minDate", None):
		query = query + "AND date >= %s "
		parameters.append(kwargs["minDate"])

	if kwargs.get("maxDate", None):
		query = query + "AND date <= %s "
		parameters.append(kwargs["maxDate"])

	if kwargs.get("minTime", None):
		query = query + "AND time >= %s "
		parameters.append(kwargs["minTime"])
	
	if kwargs.get("maxTime", None):
		query = query + "AND time <= %s "
		parameters.append(kwargs["maxTime"])
	
	
	paraTuple = tuple(parameters)
	
	cur = db.cursor()
	
	cur.execute(query, paraTuple)
	
	results = cur.fetchall()
	
	cur.close()

	return results

def main():
	quickReport()	

if __name__ == "__main__":
	main()
