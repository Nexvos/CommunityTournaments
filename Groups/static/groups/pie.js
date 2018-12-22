// //svg size variables - also controls size of pie --- Trying to make the pie page size reactive
var w= (document.getElementsByClassName('jumbotron')[0].clientWidth) * 0.42;
var wOffset = (document.getElementsByClassName('jumbotron')[0].clientWidth) * 0.5;
console.log(w);
console.log(wOffset);
var h= w *0.75;
//Set outer and inner radius of the donut
var outerRadiusTeam=(Math.min(w, h) / 2) -1;
var innerRadius=outerRadiusTeam *0.78;
var outerRadius=outerRadiusTeam *0.88;

// //legend variables
var legendRectSize=20;
var legendSpacing=7;
var legendHeight=legendRectSize+legendSpacing;


//sorting function
var sort_by;

(function() {
    // utility functions
    var default_cmp = function(a, b) {
            if (a == b) return 0;
            return a < b ? -1 : 1;
        },
        getCmpFunc = function(primer, reverse) {
            var dfc = default_cmp, // closer in scope
                cmp = default_cmp;
            if (primer) {
                cmp = function(a, b) {
                    return dfc(primer(a), primer(b));
                };
            }
            if (reverse) {
                return function(a, b) {
                    return -1 * cmp(a, b);
                };
            }
            return cmp;
        };

    // actual implementation
    sort_by = function() {
        var fields = [],
            n_fields = arguments.length,
            field, name, reverse, cmp;

        // preprocess sorting options
        for (var i = 0; i < n_fields; i++) {
            field = arguments[i];
            if (typeof field === 'string') {
                name = field;
                cmp = default_cmp;
            }
            else {
                name = field.name;
                cmp = getCmpFunc(field.primer, field.reverse);
            }
            fields.push({
                name: name,
                cmp: cmp
            });
        }

        // final comparison function
        return function(A, B) {
            var a, b, name, result;
            for (var i = 0; i < n_fields; i++) {
                result = 0;
                field = fields[i];
                name = field.name;

                result = field.cmp(A[name], B[name]);
                if (result !== 0) break;
            }
            return result;
        }
    }
}());

function InitialPie(dataset, totalamount, team_dataset) {

	//sort the data
	dataset.sort(sort_by({name:'team',reverse:true},'name',{name:'amount',primer:parseInt,reverse:false}));
	team_dataset.sort(sort_by({name:'team',reverse:true}));




	//Create the SVG with correct attributes and transformed g element
	var svg=d3.select("#chart")
			.append("svg")
			.attr({
				width:w,
				height:h
			}).append('g')
			.attr({
				transform:'translate('+((w/4)+(wOffset/4))+','+h/2+')'
			});


	//Create d3 arc - This sets up the creation of the
	var arc=d3.svg.arc()
			.outerRadius(outerRadius)
			.innerRadius(innerRadius);



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
	var gt = svg.append("g")
        .attr(
            "id","gt"
        );;

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
				},
				class:'shadow'
			})
			.style("stroke", "#343a40")
            .style("stroke-width", "1");


	// Creates the pie elements
	var path=gt.selectAll('path')
			.data(pie(dataset))
			.enter()
			.append('path')
			.attr({
				d:arc,
				fill: function(d,i){
					return d.data.colour;
				},
				class:'shadow bet-path',
				opacity: 0.65
			})
			//tooltip mouseover animation
			.on("mouseover", mouseover)
			.on("mouseout", mouseout);

	//tooltip creation
	var div = d3.select("body").append("div")
		.attr("class", "tooltip")
		.style("opacity", 0);

	function mouseover(d) {
		d3.select(this).transition()
			.duration(200)
            .style("border", "black")
			.style("stroke", "white")
			.style("stroke-width", "2")
			.style("opacity", 1);
		div.transition()
			.duration(200)
			.style("opacity", .85)
			.style("height", 60 + "px")
			.style("background", d.data.colour);
		div.html("Name: " + d.data.name + "<br>" + "£" + d.data.amount.toFixed(2)+ "<br>" + d.data.team)
			.style("left", (d3.event.pageX) + "px")
			.style("top", (d3.event.pageY - 28) + "px");
		};

	function mouseout(d) {
		d3.select(this).transition()
			.duration(200)
			.style("stroke", "black")
            .style("stroke-width", "1")
			.style("opacity", 0.65);
		div.transition()
			.duration(500)
			.style("opacity", 0);
	};

	// Animation of the pie elements
	path.transition()
		.duration(800)
		.attrTween('d', function(d) {
			var interpolate = d3.interpolate({startAngle: 0, endAngle: 0}, d);
			return function(t) {
				return arc(interpolate(t));
			};
		});

	//percentage text
	var text=svg.selectAll('text')
	  .data(pie(dataset))
	  .enter()
	  .append("text")
	  .transition()
	  .duration(1000)
	  .attr("transform", function (d) {
		  return "translate(" + arc.centroid(d) + ")";
	  })
	  .attr("dy", "0.2rem")
	  .attr("text-anchor", "middle")
	  .attr("class", "strokeme")
	  .attr("id", "percentagetext")
	  .text(function(d){ if (d.data.percent>2){
		return d.data.percent.toFixed(2)+"%";
	  }})
	  ;


	//Creation of the legend
	// var legend=svg.selectAll('.legend')
	//   .data(team_dataset)
	//   .enter()
	//   .append('g')
	//   .attr({
	// 	  class:'legend',
	// 	  transform:function(d,i){
	// 		  //Just a calculation for x and y position
	// 		  return 'translate('+ (outerRadius + 30) + ',' + ((i*legendHeight) - h/2 +100) + ')';
	// 	  }
	//   });
    //
    //
	// legend.append('rect')
	//   .attr({
	// 	  width:legendRectSize,
	// 	  height:legendRectSize,
	// 	  rx:20,
	// 	  ry:20
	//   })
	//   .style({
	// 	  fill:function(d){
	// 				return d.colour;
	// 			},
	// 	  stroke:function(d){
	// 				return d.colour;
	// 			}
	//   });
    //
	// legend.append('text')
	//   .attr({
	// 	  x:30,
	// 	  y:15
	//   })
	//   .text(function(d){
	// 	  return d.team;
	//   });

	//total
	var totalLabel = svg.append("text")
		.html("Total money bet:")
		.attr({
			  class:'total',
			  transform:function(d,i){
				  //Just a calculation for x and y position
				  return 'translate(-65,' + -15 + ')';
			  }
		  });
	var total = svg.append("text")
		.html("£" + totalamount.toFixed(2))
		.attr({
			  class:'total',
			  "id":'totalMoney',
			  transform:function(d,i){
				  //Just a calculation for x and y position
				  return 'translate(-25,' + 15 + ')';
			  }
		  })





};


//button
function change(asd, ads, team_dataset) {

	//sort data by amount -> person -> team
	// asd.sort(sort_by('amount',false,parseInt));
	// asd.sort(sort_by('name',false,function(a){return a.toUpperCase()}));
	// asd.sort(sort_by('team',false,function(a){return a.toUpperCase()}));
	asd.sort(sort_by({name:'team',reverse:true},'name',{name:'amount',primer:parseInt,reverse:false}));


    var svg = d3.select("#chart")
		.select("svg")
		.select("g");

    var gs = svg.select("#gs");
    var gt = svg.select("#gt");
    // var oldData = svg.selectAll("path")
    //  .data().map(function(d) { return d.data });
    // console.log(oldData);

    var path = gt.selectAll('path');
    var pathTeam = gs.selectAll('path');

	var pie=d3.layout.pie()
			.value(function(d){return d.percent})
			.sort(null)
			.padAngle(0);
    //tooltip creation


	var arc=d3.svg.arc()
			.outerRadius(outerRadius)
			.innerRadius(innerRadius);

	var arcTeam=d3.svg.arc()
			.outerRadius(outerRadiusTeam)
			.innerRadius(innerRadius);

    path.each(function (d) {
        this._current = d;
    }); // store the initial angles
    pathTeam.each(function (d) {
        this._current = d;
    }); // store the initial angles

    path.data(pie(asd));
    path.transition().duration(750).attrTween("d", arcTween); // redraw the arcs

    pathTeam.data(pie(team_dataset));
    pathTeam.transition().duration(750).attrTween("d", arcTweenTeam);
    // console.log(asd);

    // path.data(pie(oldData))
    // 	.exit();

    $("#fadein").attr("id", "");


	// Creates the pie elements
	pathTeam.data(pie(team_dataset))
		.enter()
		.append('path')
		.attr({
			d:arcTeam,
			fill: function(d,i){
				return d.data.colour;
			},
			class: 'shadow'
		});

    path.data(pie(asd))
        .enter()
        .append('path')
        .attr({
            d: arc,
            fill: function (d) {
            	console.log(d.data.colour);
                return d.data.colour;
            },
			class: 'shadow bet-path',
            "id": "fadein",
			opacity: 0.65
        })
        //tooltip mouseover animation
        .on("mouseover", mouseover)
        .on("mouseout", mouseout);
	function update() {
	  // Update selection: Resize and position existing
	  // DOM elements with data bound to them.
	  var selection = d3.select("#gt")
		.selectAll("path").data(pie(asd))
		.style('fill', function (d) {
            	console.log(d.data.colour);
                return d.data.colour;
            });
	};
	update();



    var div = d3.select("body").append("div")
		.attr("class", "tooltip")
		.style("opacity", 0);

	function mouseover(d) {
		d3.select(this).transition()
			.duration(200)
			.style("stroke", "white")
			.style("stroke-width", "2")
			.style("opacity", 1);
		div.transition()
			.duration(200)
			.style("opacity", .85)
			.style("background", d.data.colour);
		div.html("Name: " + d.data.name + "<br>" + "£" + d.data.amount.toFixed(2))
			.style("left", (d3.event.pageX) + "px")
			.style("top", (d3.event.pageY - 28) + "px");
		};

	function mouseout(d) {
		d3.select(this).transition()
			.duration(200)
			.style("stroke", "black")
            .style("stroke-width", "1")
			.style("opacity", 0.65);
		div.transition()
			.duration(500)
			.style("opacity", 0);
	};

    path.transition().duration(750).attrTween("d", arcTween);
    pathTeam.transition().duration(750).attrTween("d", arcTweenTeam);


    $("#fadein").hide().fadeIn(3000);


    function arcTween(a) {
        var i = d3.interpolate(this._current, a);
        this._current = i(0);
        return function (t) {
            return arc(i(t));
        };
    }
    function arcTweenTeam(a) {
        var i = d3.interpolate(this._current, a);
        this._current = i(0);
        return function (t) {
            return arcTeam(i(t));
        };
    }
    //Percentage Text
	var text=svg.selectAll('#percentagetext')
	    .data(pie(asd))
	 	.enter()
		.append("text")
		.attr("id", "percentagetext");
	svg.selectAll('#percentagetext').transition()
	  .duration(1000)
	  .attr("transform", function (d) {
		  return "translate(" + arc.centroid(d) + ")";
	  })
	  .attr("dy", ".4em")
	  .attr("text-anchor", "middle")
	  .attr("class", "strokeme")
	  .text(function(d){ if (d.data.percent>2){
		return d.data.percent.toFixed(2)+"%";
	  }})
	  ;


		//Creation of the legend
	// var legend=svg.selectAll('.legend')
	//   .data(color.domain())
	//   .enter()
	//   .append('g')
	//   .attr({
	// 	  class:'legend',
	// 	  transform:function(d,i){
	// 		  //Just a calculation for x and y position
	// 		  return 'translate('+ (outerRadius + 30) + ',' + ((i*legendHeight) - h/2 +100) + ')';
	// 	  }
	//   });
    //
	// legend.append('rect')
	//   .attr({
	// 	  width:legendRectSize,
	// 	  height:legendRectSize,
	// 	  rx:20,
	// 	  ry:20
	//   })
	//   .style({
	// 	  fill:color,
	// 	  stroke:color
	//   });
    //
	// legend.append('text')
	//   .attr({
	// 	  x:30,
	// 	  y:15
	//   })
	//   .text(function(d){
	// 	  return d;
	//   });


	//adjust total
	svg.select("#totalMoney")
		.html("£" + ads.toFixed(2));
};

