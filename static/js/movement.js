/* global $ */

var drive = {
	mode: 'none',
	power: 0,
	left: 0,
	right: 0,
	turn: 'none'
};
var turret = {
	pitch: 0,
	yaw: 0
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

	switch (event.key) {
		case 'ArrowUp':
			turret.pitch = 'up';
			break;
		case 'ArrowDown':
			turret.pitch = 'down';
			break;
		case 'ArrowLeft':
			turret.yaw = 'left';
			break;
		case 'ArrowRight':
			turret.yaw = 'right';
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

	// Initialize socket
	socket = new WebSocket('ws://' + window.location.hostname + ':8081');
	socket.onopen = function() {
		console.log('connected');
		setInterval(function() {
			drive.mode = getDriveMode();
			var output = {drive: drive, turret: turret};
			console.log(output);
			socket.send(JSON.stringify(output));
		}, 50);
	}
});;
