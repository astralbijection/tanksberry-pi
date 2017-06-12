/* global $ */

const TURN_REDUCTION = 0.2;

var socket;

function getDriveMode() {
	return $('#driveconfig input[name=drivemode]:checked').val();
}

function invertBackwards() {
	return $('#driveconfig input[name=invertBack]').is(':checked');
}

var tankDrive = {
	left: 0,
	right: 0,
	keyDown: function(event) {
		switch (event.key) {
		case 'q':
			tankDrive.left = 1;
			break;
		case 'a':
			tankDrive.left = -1;
			break;
		case 'e':
			tankDrive.right = 1;
			break;
		case 'd':
			tankDrive.right = -1;
			break;
		default:
			break;
		}
	},
	keyUp: function(event) {
		switch(event.key) {
		case 'q': case 'a':
			tankDrive.left = 0;
			break;
		case 'e': case 'd':
			tankDrive.right = 0;
			break;
		default:
			break;
		}
	},
	output: function() {
		return {left: tankDrive.left, right: tankDrive.right};
	}
};
var wasdDrive = {
	power: 0,
	turn: 'none',
	keyDown: function(event) {
		switch (event.key) {  
		case 'w':
			wasdDrive.power = 1;
			break;
		case 's':
			wasdDrive.power = -1;
			break;
		case 'a':
			wasdDrive.turn = 'left';
			break;
		case 'd':
			wasdDrive.turn = 'right';
			break;
		default:
			break;
		}
	},
	keyUp: function(event) {
		switch (event.key) {
		case 'w': case 's':
			wasdDrive.power = 0;
			break;
		case 'a': case 'd':
			wasdDrive.turn = 'none';
			break;
		default:
			break;
		}
	},
	output: function() {
		var left = wasdDrive.power, right = wasdDrive.power;
		if (wasdDrive.power !== 0) {  // Moving forwards or backwards
			if (wasdDrive.power < 0 && invertBackwards()) {  // Swap left and right if necessary
				if (wasdDrive.turn == 'right') {
					wasdDrive.turn = 'left';
				} else if (wasdDrive.turn == 'left') {
					wasdDrive.turn = 'right';
				}
			}
			switch (wasdDrive.turn) {  // Reduce power to the side we are turning to
			case 'left':
				left *= TURN_REDUCTION;
				break;
			case 'right':
				right *= TURN_REDUCTION;
				break;
			default:
				break;
			}
		} else {  // Robot staying in place
			switch (wasdDrive.turn) {  // Invert for a point turn
			case 'left':
				left *= -1;
				break;
			case 'right':
				right *= -1;
				break;
			default:
				break;
			}
		}
		return {left: left, right: right};
	}
};
var driveModes = {
	tank: tankDrive,
	wasd: wasdDrive
};

$(function() {

	$(document).keydown(function(event) {
		var mode = driveModes[getDriveMode()];
		mode.keyDown(event);
		var output = mode.output();
		console.log(output);
		socket.send(JSON.stringify(['drive', output]));
	}).keyup(function(event) {
		var mode = driveModes[getDriveMode()];
		mode.keyUp(event);
		var output = mode.output();
		console.log(output);
		socket.send(JSON.stringify(['drive', output]));
	});

	// Initialize socket
	socket = new WebSocket('ws://' + window.location.host + '/socket');
	socket.onopen = function() {
		console.log('connected to robot');
	};
});
