//<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
function chartDraw(total, fiveMin, tenMin, fifteenMin, missed){


google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);

function drawChart(){
  var data = google.visualization.arrayToDataTable([
  ['Tasks', 'Hours Per Day'],
  ['On Time', total - (fiveMin + tenMin + fifteenMin + missed)],
  ['First 5 Minutes', fiveMin],
  ['First 10 Minutes', tenMin],
  ['First 15 Minutes', fifteenMin],
  ['Missed', missed]
]);

//optional: add a title and set the width and height of the chart.
var options = { titleTextStyle:{ fontSize:20 }, colors: ['lime', 'springgreen', 'yellow', 'orange', 'red'], 'width':400, 'height':500};
  
  // Display the chart inside the <div> element with id="piechart"
  var chart = new google.visualization.PieChart(document.getElementById('piechart'));
  chart.draw(data, options);
}


}

function drawLineChart(){
	
google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);

	function drawChart(){

	//get the JSON Data...this code is taken directly from https://developers.google.com/chart/interactive/docs/php_example
	$.get("/updateCheckinHistory", function(jsonData){

		var data = new google.visualization.DataTable(jsonData);
		var options = {colors: ['lime', 'red', 'springgreen', 'yellow', 'orange'],
'width': 800, 
'height':400,
legend: {position: 'right'}}
		var chart = new google.visualization.LineChart(document.getElementById("linechart"));
		chart.draw(data,options);
})


	}
}


function drawCalendar(isAdmin) {
	$('#calendar').fullCalendar({
		defaultView: "agendaWeek",
                        theme: "standard",      
                        header: {// https://stackoverflow.com/questions/25681573/fullcalendar-header-buttons-missing
                                left: "agendaWeek,agendaDay",   
                                center: "title",
                                right: "prev,today,next"
                        },
			
			nowIndicator : true,
 
			eventOrder: "location",

                        eventRender: function(event, element){

                                element.qtip({
                                        content: event.description
                                });
                        
                         

                        },

			eventSources: [
				"/shiftCalendarData",
			[{
			title: "Trevor",
			dow: [1, 7],
			start: '18:00',
			end: '21:00',
			description: "Trevor Freeland- 815-762-5648",
			color: "tan",
			location: "SAS"

			},

			{
			title: "Eileen",
			dow: [1, 7],
			start: '21:00',
			end: '24:00',
			description: "Eileen Lower- 928-821-0702",
			color: "tan",
			location:"SAS"

			},

			{
			title: "Kevin",
			dow: [2, 4],
			start: '18:00',
			end: '21:00',
			description: 'Kevin Tran- 651-356-9496', 
			color: "tan",
			location: "SAS"

			},

			{
			title: "AVAIL->STAFF",
			dow: [2, 4],
			start: '21:00',
			end: '24:00',
			description: "Jump to next stage of escalation procedure.", 
			color: "tan",
			location: "SAS"

			},

			{
			title: "AVAIL->STAFF",
			dow: [6],
			start: '18:00',
			end: '21:00',
			description: "Jump to next stage of escalation procedure.", 
			color: "tan",
			location: "SAS"

			},

			{
			title: "Evie",
			dow: [3],
			start: '20:00',
			end: '23:00',
			description: "Evie Odden- 612-999-5119.", 
			color: "tan",
			location: "SAS"

			},

			{
			title: "Melanie",
			dow: [5],
			start: '18:00',
			end: '21:00',
			description: "Melanie Bullock-510-688-2824", 
			color: "tan",
			location: "SAS"

			},

			{
			title: "Amida",
			dow: [6],
			start: '12:00',
			end: '15:00',
			description: "Amida McNulty- 480-620-4911", 
			color: "tan",
			location: "SAS"

			},

			{
			title: "Katherine",
			dow: [6],
			start: '15:00',
			end: '18:00',
			description: "Katherine Jackson- 773-575-9615", 
			color: "tan",
			location: "SAS"

			},

			{
			title: "Ethan",
			dow: [7],
			start: '12:00',
			end: '15:00',
			description: "Ethan Ta- 952-649-1301", 
			color: "tan",
			location: "SAS"

			},

			{
			title: "Melanie",
			dow: [7],
			start: '15:00',
			end: '18:00',
			description: "Melanie Bullock- 510-688-2824", 
			color: "tan",
			location: "SAS"

			},
		
			{
			title: "TEST",
			start:"2018-09-28T23:00",
			end:"2018-09-28T00:00",
			description: "A test event. Do not disturb.",
			location:"nowhere",
			color: "green"
			}

			]
		]
                
	 });
	
	if (isAdmin){
		$('#calendar').fullCalendar('option', {
			eventClick: function(event){
			window.location.href="/shiftDetails?shiftID=" + event.id} //https://stackoverflow.com/questions/16959476/how-to-go-to-a-url-using-jquery
		});
	}
		
	$('#calendar').fullCalendar('rerenderEvents');	
	//$.get("/shiftCalendarData", function(data){

	//	//render on the current hour.
	//	var currHour = new Date().getHours();                
	//	$('#calendar').fullCalendar('option', {
	//		firstHour: currHour
	//	});	
			

	
//	
	
//	$('#calendar').fullCalendar('addEventSource', data);

//        });

	

}

