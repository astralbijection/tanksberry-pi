/* global $ */

var power = 0;
var turn = 'none';

$(document).keydown(function(event) {
	switch (event.key) {
	case 'w':
		power = 1;
		break;
	case 's':
		power = -1;
		break;
	case 'a':
		turn = 'left';
		break;
	case 'd':
		turn = 'right';
		break;
	}
}).keyup(function(event) {
	switch (event.key) {
	case 'w': case 's':
		power = 0;
		break;
	case 'a': case 'd':
		turn = 'none'
		break;
	}
});


var socket;


$(function() {
	socket = new WebSocket('ws://localhost:8081');
	socket.onopen = function() {
		setInterval(function() {
			socket.send(JSON.stringify({drive: {mode: 'wasd', power: power, turn: turn}, turret: {}}));
		}, 50);
	}
});