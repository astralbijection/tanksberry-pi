/* global $ */

var drive = {
	mode: 'none',
	power: 0,
	left: 0,
	right: 0,
	turn: 'none'
};
var turret = {

};

function getDriveMode() {
	return $('#driveconfig input[name=drivemode]:checked').val();
}

$(document).keydown(function(event) {

	switch (getDriveMode()) {
	case 'wasd':
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
		break;
	case 'tank':
		switch (event.key) {
		case 'q':
			drive.left = 1;
			break;
		case 'a':
			drive.left = -1;
			break;
		case 'e':
			drive.right = 1;
			break;
		case 'd':
			drive.right = -1;
			break;
		}
		break;
	}
}).keyup(function(event) {
	switch (getDriveMode()) {
	case 'wasd':
		switch (event.key) {
		case 'w': case 's':
			drive.power = 0;
			break;
		case 'a': case 'd':
			drive.turn = 'none'
			break;
		}
		break;
	case 'tank':
		switch(event.key) {
		case 'q': case 'a':
			drive.left = 0;
			break;
		case 'e': case 'd':
			drive.right = 0;
			break;
		}
		break;
	}
});


var socket;


$(function() {
	socket = new WebSocket('ws://' + window.location.hostname + ':8081');
	socket.onopen = function() {
		console.log('connected');
		setInterval(function() {
			socket.send(JSON.stringify({mode: getDriveMode(), turret: turret}));
		}, 50);
	}
});
