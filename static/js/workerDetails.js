function updatePieChart(days, employeeID){ //Days will be an integer that says over how many days to show checkin time.
//We may have to overload this operator eventually?
//How this method will work: given the current day, subtract however many days from it, and then call a get method...


	$.get('/updatePieChart', {'days':days, 'employeeID':employeeID}, function(data){

		var total = data.total;
		var missed = data.missed;
		var fiveMin = data.fiveMin;
		var tenMin = data.tenMin;
		var fifteenMin = data.fifteenMin;

		chartDraw(total, fiveMin, tenMin, fifteenMin, missed)



	})




	


}

function toggleColVis(checkBox){
	var colName = checkBox.value;
	//console.log(colName)
	var parentDiv = $(checkBox).closest("div") //Traverses DOM and gets the first parent that is a div.
	parentDiv = checkBox.parentNode.parentNode;
	//console.log(parentDiv.id)
	//get all things in that column....
	var theColumn = parentDiv.querySelectorAll("." + colName);
	console.log(checkBox.checked)	
	if (checkBox.checked == false){ //Make all the things hidden.
	for (var i = 0; i < theColumn.length; i++){
	theColumn[i].classList.add('td-hidden');
		}
	}
	else {

	for (var i = 0; i < theColumn.length; i++){
	theColumn[i].classList.remove('td-hidden');
	}

		}

//console.log(theColumn)
	
	//$(theColumn).hide();
}
