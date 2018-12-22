// //svg size variables - also controls size of pie --- Trying to make the pie page size reactive
var w= 120;
var h= 120;

//Set outer and inner radius of the donut
var outerRadiusTeam=(Math.min(w, h) / 2) -1;
var innerRadius=outerRadiusTeam *0.78;
var outerRadius=outerRadiusTeam *0.90;



function InitialPie(team_dataset, chartID) {

	//Create the SVG with correct attributes and transformed g element
	var svg=d3.select("#chart" + chartID)
			.append("svg")
			.attr({
				width:w + "px",
				height:h + "px"
			}).append('g')
			.attr({
				transform:'translate('+w/2+','+h/2+')'
			});


	//Create pie
	var pie=d3.layout.pie()
			.value(function(d){return d.percent})
			.sort(null)
			.padAngle(0);

		//team pie
	var gs = svg.append("g")
        .attr(
            "id","gs"
        );

	var arcTeam=d3.svg.arc()
			.outerRadius(outerRadiusTeam)
			.innerRadius(innerRadius);



	// Creates the pie elements
	var pathTeam=gs.selectAll('path')
			.data(pie(team_dataset))
			.enter()
			.append('path')
			.attr({
				d:arcTeam,
				fill: function(d,i){
					return d.data.colour;
				}
			})
			.style("stroke", "#9a9b9c")
            .style("stroke-width", "1");





};

