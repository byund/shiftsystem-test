import MySQLdb
from dbFunctions import dbLogIn



def quickReport(lowerBound, upperBound): #Take in lowerbound and upper bound datetimes.
	
	db = dbLogIn()
	cur = db.cursor()
	cur.execute("Call quickReport(%s, %s)", (upperBound, lowerBound))
	results = cur.fetchall()
	#Results is a set of tuples, each tuple-row is of the form employeeID, shiftID, firstName, lastName, date, startTime, checkinTime
	cur.close()
	db.close()
	
	return results;

def quickWorkerSummary(db, lowerBound, upperBound, employeeID): #Gets a quick report, except for a given worker.
	cur = db.cursor()
	cur.execute("CALL quickWorkerSummary(%s, %s, %s)", (upperBound, lowerBound, employeeID))
	results = cur.fetchall()
	cur.close()
	
	return results;

def main():
	return

if __name__ == "__main__":
	main()	
