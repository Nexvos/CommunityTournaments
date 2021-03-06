var data = [4, 8, 15, 16, 23, 42];

var width = 960,
    height = 500;

var y = d3.scale.linear()
    .domain([0, d3.max(data)])
    .range([height, 0]);


var chart = d3.select(".chart")
    .attr("width", width)
    .attr("height", height);

var barWidth = width / data.length;

var bar = chart.selectAll("g")
    .data(data)
    .enter().append("g")
    .attr("transform", function(d, i) {return "translate(" + i * barWidth + ", 0)"; });


bar.append("rect")
  .attr("y", function(d) { return y(d); })
  .attr("height", function(d) { return height - y(d); })
  .attr("width", barWidth - 1);

bar.append("text")
      .attr("x", barWidth / 2)
      .attr("y", function(d) { return y(d) + 3; })
      .attr("dy", "1.75em")
      .text(function(d) {return d;});

