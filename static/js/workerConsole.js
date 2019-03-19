//A file that handles all the javascript for the workerConsole frontend.

function getCurrentTime(){ //A function to get the current time from the system. Note that this function gets its time from the client-side machine, while the python method gets it from the server machine.
      var currentTime = new Date();
      var currentHour = currentTime.getHours();
      var currentMinute = currentTime.getMinutes();
      var currentSecond = currentTime.getSeconds();

      currentMinute = (currentMinute < 10 ? "0" : "") + currentMinute; //Look up ternary operator to explain why this works. It's an efficient way to write shorthand.
      currentHour = (currentHour < 10 ? "0" : "") + currentHour;

      currentSecond = (currentSecond < 10 ? "0" : "") + currentSecond;

      var currentTimeString = currentHour + ":" + currentMinute + ":" + currentSecond;

      return currentTimeString
     }

function updateClock(){ // A function to update the clock.
      
      currentTimeString = getCurrentTime()
      document.getElementById("checkinClock").firstChild.nodeValue = currentTimeString;
  }

function checkIn(employeeID, shiftID){ //A function to check in a worker.

  
  var theButton = document.getElementById("checkinButton")
  //First, disable the button.
  theButton.disabled = true;    
  theButton.innerText = "Checking you in..";

  // console.log(employeeID)
  // console.log(shiftID)

    checkinData = {"employeeID": employeeID, "shiftID": shiftID}
    $.post("/checkin", checkinData, function(data){
    
    //Assuming the checkin Succeeds.
    theButton.innerText = "Checked In " + data.checkInTime

  } ) //This goes and uses AJAX to post to the server and call the python method frontendcheckin()

  

}


function requestUnrequestSub(element, shiftID, employeeID){
  if (element.value == "subRequested" ) {//In this case, we are unrequesting a sub.
    $.post("/unrequestSub", {"shiftID": shiftID, "employeeID": employeeID})

    element.innerText = "Request Sub";

    element.style.background = "#4CAF50";

    element.value = "subUnrequested" //update button value to reflect that we unrequested a sub.
  }

  else if (element.value == "subUnrequested"){ //In this case, we must request a sub.
    $.post("/requestSub", {"shiftID": shiftID, "employeeID": employeeID})

    element.innerText = "Unrequest Sub";

    element.style.background = "#b30000";

    element.value = "subRequested" //update button value to reflect that we requested a sub.
  }

  //$.get('/')
}


function deleteSubbableShiftRow(shiftID, employeeID){
  var table = document.getElementById("subbableShiftTable")
  rowIndex = table.rows.length; //Get the length of the table.

  postData = {"shiftID":shiftID, "employeeID":employeeID}
  $.get("/getSubRequestStatus", postData, function(data){ //If sub is filled, then we will delete the row that it originally came from.
      //TODO: Figure out how to deal with this and JSON.
      
      var subFilled = data.subFilled;
      var subRequested = data.subRequested;
      //If a sub has been filled or the request has been rescinded, we must delete the row.
      if (subFilled == 1 || subRequested == 0){
        table.deleteRow(rowindex)
      } 
     


    }, "json" )

}


function insertNewSubbableShiftRow(shiftID, origEmployeeID){
  var table = document.getElementById("subbableShiftTable")
  rowIndex = table.rows.length; //Get the length of the table.

  // console.log(shiftID)
  // console.log(origEmployeeID)
  //How this will work:
  //submit an AJAX call to get the data from the row specified by shiftID and origEmployeeID.
  
  $.get('/getSubShiftInfo', {"shiftID":shiftID, "origEmployeeID":origEmployeeID}, function (data){ 

    //First, check that the shift is still requesting a sub:
    if (data.subRequested == true){//if yes, then go ahead and insert a row into the open shifts.

    var time = data.time
    var location = data.location
    var date = data.date
    
    var day = data.day
    var employeeName = data.employeeName
    var employeeID = data.employeeID
    var subButton = document.createElement("button");
    subButton.className = "button";
    subButton.value = "pickupSub";
    subButton.id = "subButton_shift_" + shiftID + "_emp_" + origEmployeeID;
    subButton.onclick = function(){pickupDropSub(subButton, employeeID);}



    //Once you have the data, create a row and insert the necessary data.

    var row = table.insertRow(rowIndex);
    var cell1 = row.insertCell(0)
    var cell2 = row.insertCell(1)
    var cell3 = row.insertCell(2)
    var cell4 = row.insertCell(3)
    var cell5 = row.insertCell(4)
    var cell6 = row.insertCell(5)

    
    cell1.innerHTML = time
    cell2.innerHTML = location
    cell3.innerHTML = date
    cell4.innerHTML = day
    cell5.innerHTML = employeeName
    cell6.appendChild(subButton);

    if (data.subbable == false){//Disable button if it's for a shift of the logged in user.
      subButton.disabled = true;
      subButton.innerHTML = "Your Shift";

    }
    else{
      subButton.innerHTML = "Sub?"
      subButton.disabled = false;
    }


    }

    


  }, "json")

  


}

function pickupDropSub(theButton, subEmployeeID){
  //Check if you're clicking to pick up a sub.
  console.log(theButton.id)
  var idArray =  theButton.id.split("_");
  var origEmployeeID = idArray[4]
  var shiftID = idArray[2]
  //var subEmployeeID = 1001 //This is a placeholder, we must put it as an input eventually.

  //store the row of the button as well.
  var parentCell = theButton.parentElement
  var parentRow = parentCell.parentElement
  var parentRowIndex = parentRow.rowIndex;



  var postData = {"origEmployeeID":origEmployeeID, "subEmployeeID":subEmployeeID, "shiftID":shiftID}
  //var postData = JSON.stringify(postData)


  
  if (theButton.value == "pickupSub"){ //on clicking you will pick up a sub.
    
    $.post('/pickupSub', postData, function(response){console.log(response.Response)})
    
   // theButton.innerText = "Subbing";

   // theButton.value = "dropSub" //update button value to reflect that we unrequested a sub.
    
   // theButton.disabled = true;
    table = document.getElementById("subbingShiftTable");

    var newRow = table.insertRow();

    for (i = 0; i < 5; i++){
      //iterate through every cell in parent row and copy information over.
      var cell = newRow.insertCell(i)
      cell.innerHTML = parentRow.cells[i].innerHTML
    }

    var lastCell = newRow.insertCell(5);
    var newButton = document.createElement('button')
    newButton.className = "button";

    lastCell.appendChild(newButton)
    newButton.value = "dropSub";
    newButton.id = "subbingButton_shift_" + shiftID + "_emp_" + origEmployeeID;
    newButton.onclick = function(){pickupDropSub(newButton, subEmployeeID)}
    newButton.innerText = "Drop"
    


    document.getElementById("subbableShiftTable").deleteRow(parentRowIndex)

    //Consider also dropping the row that the button exists in. Or not-currently it'll be autodropped as the refreshSubbableShifts method runs.
  }
  else if (theButton.value == "dropSub"){ //On clicking you will drop a sub.
      
    $.post('/dropSub', postData, function(response){console.log(response.Response)})
    //theButton.innerText = "Sub?";

    //theButton.value = "pickupSub" //update button value to reflect that we unrequested a sub.

    document.getElementById("subbingShiftTable").deleteRow(parentRowIndex) //delete the row from subbing shifts table.

    
    table = document.getElementById("subbableShiftTable");

    var newRow = table.insertRow();

    for (i = 0; i < 5; i++){
      //iterate through every cell in parent row and copy information over.
      var cell = newRow.insertCell(i)
      cell.innerHTML = parentRow.cells[i].innerHTML
    }

    var lastCell = newRow.insertCell(5);
    var newButton = document.createElement('button')
    newButton.className = "button";

    lastCell.appendChild(newButton)
    newButton.value = "pickupSub";
    newButton.id = "subButton_shift_" + shiftID + "_emp_" + origEmployeeID;
    newButton.onclick = function(){pickupDropSub(newButton, subEmployeeID)}
    newButton.innerText = "Pickup"
    


   // document.getElementById("subbingShiftTable").deleteRow(parentRowIndex)
  }

  

  //Once all is said and done, you will drop the row from the table. The reason is simple: if you are picking up a sub, then the row is in the subbableshifts table, and you must drop the row to prevent the user from clicking it again.
  //If you are dropping a sub, then you have a row in the subbingShifts table that you must drop because you are no longer subbing it.
  //Table.deleteRow(parentRow.rowIndex);
}


function switchLocation(button){//When you click the radio button you should switch.

  var location = button.value //Either "CMC" or "ResearchIT"
  //console.log(location)
  //console.log(button.id)


  $.get("/switchLocation", {"location":location}, function(data){
    //Get the data about the new shift.
    if (data.shiftExists != false){// if there is indeed a shift.

    var checkInTime = data.checkInTime; //when the employee actually checked in.
    var checkedIn = data.checkedIn;
    var checkinButton = document.getElementById("checkinButton")

    if (checkedIn){// if employee is checked in, change checkin button's text to the checkin time.
      checkinButton.innerHTML = checkInTime;
      checkinButton.disabled = true; //Also disable the button from being clicked again.

    }

    //regardless of all that, change the text on the homepage to reflect that we have chosen a different location.



  }

  document.getElementById("locationText").innerHTML = "You are currently in " + location; 

  }, "json")

}


function addShiftNotes(){

para = document.getElementById("notesPara");
//first create a form...
noteForm = document.createElement('form');
noteForm.action = "/shiftNotes";
noteForm.method = "post";
noteForm.id = "noteForm";

//set event listeners...
noteForm.addEventListener("submit", function(event){



	
	//prevent form submission.
	event.preventDefault();
	//serialize form data.
	var formData = $(this).serialize();

	//POST!
	$.post("/shiftNotes", formData, function(data){getShiftNotes() })





})

inputDiv = document.createElement('div');

noteInput = document.createElement('input');
noteInput.type = "text";
noteInput.id = "noteInputField";
noteInput.name = "note_input";
noteInput.classList.add('notesInput');
inputDiv.appendChild(noteInput);

//create the submission button...

buttonDiv = document.createElement('div');

submitButton = document.createElement('button');
submitButton.type = "submit";
submitButton.textContent = "Submit";

cancelButton = document.createElement('button');
cancelButton.textContent = "Cancel";
cancelButton.onclick = function(){getShiftNotes()};

buttonDiv.appendChild(submitButton);
buttonDiv.appendChild(cancelButton);

noteForm.appendChild(inputDiv);
noteForm.appendChild(buttonDiv);

//clear the div...
para.removeChild(document.getElementById("notesButton"))

//append form.
para.appendChild(noteForm);
}


function getShiftNotes(){
para = document.getElementById("notesPara")
//remove all children of para
	while (para.firstChild){
		
		para.removeChild(para.firstChild);
	
	}
	
	$.get('/shiftNotes', function(data){
		if (data.notes){
		para.textContent = data.notes;
			
		}
		else{
		notesButton = document.createElement('button');
		notesButton.id = "notesButton";
		notesButton.textContent = "I have an excuse!";
		notesButton.classList.add('button');
		notesButton.onclick = function(){addShiftNotes()};	
	
		para.appendChild(notesButton);

		}
			

	})


}







//window.onload = updateClock();
//window.onload = enableDisableCheckin(checkedIn, checkInTime)
window.setInterval('updateClock()', 1000)


document.addEventListener("DOMContentLoaded", function(){

drawCalendar(false);

})






//https://stackoverflow.com/questions/12693947/jquery-ajax-how-to-send-json-instead-of-querystring
//https://stackoverflow.com/questions/6587221/send-json-data-with-jquery

//https://stackoverflow.com/questions/14908864/how-can-i-use-data-posted-from-ajax-in-flask

