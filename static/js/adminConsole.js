//a file that handles all the javascript for the adminConsole frontend

function getCurrentShiftInfo(){
	$.get("/currentUpcomingShiftInfo", function(shiftInfoDic){
		console.log(shiftInfoDic)
	containerDiv = document.getElementById("currentShiftDiv")
	 //https://stackoverflow.com/questions/4968406/javascript-property-access-dot-notation-vs-brackets
	//See also: https://codeburst.io/javascript-quickie-dot-notation-vs-bracket-notation-333641c0f781
	for(var shiftID in shiftInfoDic){
		var shiftInfo = shiftInfoDic[shiftID];
		//https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Client-side_web_APIs/Manipulating_documents
		var infoDiv = document.createElement('div')
		
		//append the header for the locations...
		var locHeader = document.createElement('h4');
		locHeader.textContent = shiftInfo.location;	
		infoDiv.appendChild(locHeader);
		
		//append headers for time...
		var time = document.createElement('h4')
		time.textContent = shiftInfo.startTime + " - " + shiftInfo.endTime
		infoDiv.appendChild(time);


		//append the list of employees...
		var employeeDic = shiftInfo.employees;
		console.log(employeeDic)
		var employeeList = document.createElement('ul');
		for (id in employeeDic){//id will be a number, so you must use bracket notation...
			//Check for subs..
			if (employeeDic[id].subEmployee){
			var subEmployeeDic = employeeDic[id].subEmployee;

			var subEmployee = document.createElement('li');
			var subEmployeeLink = document.createElement('a');
			
			subEmployeeLink.textContent = subEmployeeDic.name;
			subEmployeeLink.href = "/workerDetails?workerSelector=" + subEmployeeDic.id;
			subEmployee.appendChild(subEmployeeLink);
			
		
			var employee = document.createElement('li');
			employee.textContent = "Subbing for "
			var employeeLink = document.createElement('a');
			employeeLink.textContent = employeeDic[id].name;
			employeeLink.href = "/workerDetails?workerSelector=" + id;
			
			employee.appendChild(employeeLink);

			var sublist = document.createElement('ul');
			sublist.appendChild(employee);
			
			subEmployee.appendChild(sublist);

			
			employeeList.appendChild(subEmployee);	
			}
			
			else{
			var employee = document.createElement('li');
			var employeeLink = document.createElement('a');
			employeeLink.textContent = employeeDic[id].name;
			employeeLink.href = "/workerDetails?workerSelector=" + id;
			

			
			employee.appendChild(employeeLink);
			employeeList.appendChild(employee);
			}

			}
		infoDiv.append(employeeList);
	

		containerDiv.appendChild(infoDiv)

}


}, "json")




}


window.onload= drawLineChart();
