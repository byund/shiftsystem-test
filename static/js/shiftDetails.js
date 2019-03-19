function searchShifts(){ 
	var form = document.getElementById("searchCriteria");
	var searchCriteria = new FormData(form);	

	//var xhr = new XMLHttpRequest;
	//xhr.open('POST', '/searchShifts', true);
	//xhr.send(searchCriteria);
	$.ajax({type:"POST",
	url:"/searchShifts", 
	data: searchCriteria, 
	contentType: false, //https://www.mattlunn.me.uk/blog/2012/05/sending-formdata-with-jquery-ajax/
	processData: false,
	success: function(data){
		
		var resultsList = document.getElementById("resultsList");
		//resultsDiv.removeChild(document.getElementById("searchResults"));
		resultsList.innerHTML=""; //https://stackoverflow.com/questions/683366/remove-all-the-children-dom-elements-in-div
		//var resultsList = document.createElement('ul');	
		var shiftIDs = data.shifts;
	
		for (i=0; i<shiftIDs.length; i++){
			var shiftID = shiftIDs[i];
	
			var result = document.createElement('li');
			var resultButton = document.createElement('button');
			resultButton.classList.add("resultButton");
			resultButton.textContent = shiftID;
			resultButton.id = shiftID;
		//resultButton.href="/shiftDetails?shiftID=" + shiftID;
		//resultButton.href="";
			resultButton.onclick = shiftDetailButton;
		 //https://stackoverflow.com/questions/688196/how-to-use-a-link-to-call-javascript
			result.appendChild(resultButton);

			resultsList.appendChild(result);	
	

			}			

		//resultsDiv.appendChild(resultsList);
		function shiftDetailButton(){
			var shiftID = this.id;
			getShiftDetails(shiftID);
		}


		}	


	



})

}

function getShiftDetails(shiftID){
	console.log(shiftID)
	$.get("/getShiftDetails", {"shiftID":shiftID}, function(shiftData){
		console.log(shiftData)
		//Prep the ShiftInfo Div...

		shiftInfoDiv = document.getElementById("shiftInfoDiv");
		//shiftInfoDiv.innerHTML=""; DON"T DO THIS. See https://stackoverflow.com/questions/3955229/remove-all-child-elements-of-a-dom-node-in-javascript for details.
		while (shiftInfoDiv.firstChild){ //https://developer.mozilla.org/en-US/docs/Web/API/Node/childNodes
				shiftInfoDiv.removeChild(shiftInfoDiv.firstChild)
		}
		var shiftHeader = document.createElement('h3');
		shiftHeader.textContent = "Shift Info";
		shiftInfoDiv.appendChild(shiftHeader);
	
		var shiftDetails =shiftData[shiftID];
		
		idPara = document.createElement('p');
		idPara.id = "idPara";
		idPara.textContent = "ID " + shiftID;

		var startTime = document.createElement('p');
		startTime.id = "startTime";
		startTime.textContent = "Start Time: " + shiftDetails["startTime"];

		var endTime = document.createElement('p');
		endTime.id = "endTime";
		endTime.textContent = "End Time: " + shiftDetails["endTime"];

		var location = document.createElement('p');
		location.id = "location";
		location.textContent = "Location: " + shiftDetails["location"]
		
		var date = document.createElement('p');
		date.id ="date";
		date.textContent = "Date: " + shiftDetails["date"];
		
		var day = document.createElement('p');
		day.id = "day";
		day.textContent = "Day: " + shiftDetails["day"];		
		
		shiftInfoDiv.appendChild(idPara);
		shiftInfoDiv.appendChild(date);
		shiftInfoDiv.appendChild(day);
		shiftInfoDiv.appendChild(startTime);
		shiftInfoDiv.appendChild(endTime);
		shiftInfoDiv.appendChild(location);
		
		//next, clear the employeeInfoDiv....	
		var employeeInfoDiv = document.getElementById("employeeInfoDiv");
		while (employeeInfoDiv.firstChild){
			employeeInfoDiv.removeChild(employeeInfoDiv.firstChild);
		}
		var employeeHeader = document.createElement('h3')
		employeeHeader.textContent = "Employees"
		employeeInfoDiv.appendChild(employeeHeader);

		//now get all the info of the employees.	
		var employeeDic = shiftDetails.employees
		var employeeList = document.createElement('ul')	
		employeeList.id = "employeeList";

		for (id in employeeDic){
		var employee = employeeDic[id];
		
		//employeeInfo shall hold all the info we have on an employee.
		var employeeInfo = document.createElement('li');
		employeeInfo.id = id;

		var employeeLink = document.createElement('a');
		employeeLink.textContent = employee.name;
		employeeLink.href="/workerDetails?workerSelector=" + id;
		
		employeeInfo.appendChild(employeeLink);
		
		var details = document.createElement('p');
		employeeInfo.appendChild(details);
		
		
			if (employee.subEmployee){
				//There won't be a checkin time, so populate with sub info.
				//TODO: Add when this sub was requested here.

				var subInfo =  document.createElement('p');
				subInfo.textContent = "Subbing: "
				var subID = employee.subEmployee.id;
				var subName = employee.subEmployee.name;
				
				var subEmployeeLink = document.createElement('a');
				subEmployeeLink.textContent = subName;
				subEmployeeLink.href = "/workerDetails/employeeID="+ subID;
				
				subInfo.appendChild(subEmployeeLink);
			
				details.appendChild(subInfo);
			}
			else{
				
				var info = document.createElement('p')
				
				if (employee.checkinTime){
				info.textContent = "Checked In " + employee.checkinTime;
				}
				else{
				info.textContent = "Not Checked In";	
				}
			
				details.appendChild(info);	
			}

		employeeList.appendChild(employeeInfo);
			
		}
		employeeInfoDiv.appendChild(employeeList)

		var addButton = document.createElement('button');
		addButton.textContent = "Edit Employees";
		addButton.onclick = loadEmployeeSelect;
		employeeInfoDiv.appendChild(addButton);

})



}

//Now we define a two-parter way of adding/removing workers.
//
//The first method turns the employees field into a dynamic multiselect box.

function loadEmployeeSelect(){
	//First, get a list of all the workers who are currently on this shift..
	var currentEmployees = []
	var employeeList = document.getElementById("employeeList").childNodes; //the element employeeList is a <ul> with each child <li> being an employee's info.
	for (i = 0; i < employeeList.length; i++){
		currentEmployees.push(employeeList[i].id)
	}
	
	//next, get a list of all possible employees.
	$.get('/getAllWorkers', function(allWorkers){
	
	//Once all the workers have been got, we proceed to modify the box.
	var selectionBox = document.createElement('select')
	selectionBox.id = "employeeSelect";
	selectionBox.classList.add("chosen-select");
	

	selectionBox.multiple = true;
	Object.keys(allWorkers).forEach(function(key){
		
		var selection = document.createElement('option');
		selection.value=key;
		selection.textContent = allWorkers[key];
		var keyStr = key.toString;	
		if (currentEmployees.includes(key)){ //Random, kinda relevant reading for the intrigued soul. Your question is: "Why can't you just use "if key in currentEmployees?"
		selection.selected = true;
		}
		selectionBox.appendChild(selection);	
	
				});

	//remove all children from employeeInfoDiv....
	var employeeInfoDiv = document.getElementById("employeeInfoDiv");
	while (employeeInfoDiv.firstChild){
		employeeInfoDiv.removeChild(employeeInfoDiv.firstChild);
	}
	
	//Append selection box.
	
	employeeInfoDiv.appendChild(selectionBox);
	//Apply Chosen UI
	
	$(".chosen-select").chosen();

	//create the button that will call the addUnAdd worker. And the checkbox.
	
	var followingCheckBox = document.createElement('input');
	followingCheckBox.type = "checkbox";
	followingCheckBox.id = "followingCheckBox";
	
	var checkBoxLabel = document.createElement("label");
	checkBoxLabel.textContent = "Update for all following.";
	checkBoxLabel.for = "followingCheckBox";
	
	var updateButton = document.createElement('button');
	updateButton.textContent = "Update";
	updateButton.id = "updateButton";
	updateButton.onclick = function(){
		var prevEmployees = currentEmployees;
		updateShifts(prevEmployees)

	}

	var cancelButton = document.createElement('button');
	cancelButton.textContent = "Cancel";
	cancelButton.id = "cancelButton";
	cancelButton.onclick= function(){

	var idPara = document.getElementById("idPara").textContent.split(" ");
	var shiftID = idPara[1];
	getShiftDetails(shiftID);
}
	employeeInfoDiv.appendChild(checkBoxLabel);
	employeeInfoDiv.appendChild(followingCheckBox);
	employeeInfoDiv.appendChild(updateButton);
	employeeInfoDiv.appendChild(cancelButton);	
	

	
	})	

}


function updateShifts(prevEmployees){
	//Send shiftID, time, location, current employee selection, old employee selection, and if allFollowing is checked.
	
	var idPara = document.getElementById("idPara").textContent.split(" ");
	var shiftID = idPara[1];

	var startTimePara = document.getElementById("startTime").textContent.split(" ");
	var startTime = startTimePara[2];
	
	var locPara = document.getElementById("location").textContent.split(" ");
	var location = locPara[1];

	var dayPara = document.getElementById("day").textContent.split(" ");
	var day = dayPara[1];

	var selectedEmployees = [] //An array of currently selected employeeIDs.

	var options = document.getElementById("employeeSelect").options //https://stackoverflow.com/questions/5866169/how-to-get-all-selected-values-of-a-multiple-select-box
	for (var i = 0; i < options.length; i++){
		if (options[i].selected){
		selectedEmployees.push(options[i].value)
		}	
	
	}
	
	var allFollowing = document.getElementById("followingCheckBox").checked;
	console.log(shiftID, startTime, location, prevEmployees, selectedEmployees, allFollowing);	

	$.post('/updateShifts', {"shiftID":shiftID, "day":day, "startTime":startTime, "location":location, "prevEmployees":prevEmployees, "selectedEmployees":selectedEmployees, "allFollowing":allFollowing}, function(){
getShiftDetails(shiftID);

})
}	



