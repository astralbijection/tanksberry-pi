/* global $ */

var drive = {
	mode: 'wasd',
	power: 0,
	turn: 'none'
};
var turret = {

};

$(document).keydown(function(event) {
	switch (event.key) {
	case 'w':
		drive.power = 1;
		break;
	case 's':
		drive.power = -1;
		break;
	case 'a':
		drive.turn = 'left';
		break;
	case 'd':
		drive.turn = 'right';
		break;
	}
}).keyup(function(event) {
	switch (event.key) {
	case 'w': case 's':
		drive.power = 0;
		break;
	case 'a': case 'd':
		drive.turn = 'none'
		break;
	}
});


var socket;


$(function() {
	socket = new WebSocket('ws://localhost:8081');
	socket.onopen = function() {
		setInterval(function() {
			socket.send(JSON.stringify({drive: drive, turret: turret}));
		}, 50);
	}
});