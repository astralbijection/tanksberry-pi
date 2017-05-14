var child_process = require('child_process');
var express = require('express');
var http = require('http');
var nunjucks = require('nunjucks');
var util = require('util');
var path = require('path');
var process = require('process');


const ROOT_DIR = path.normalize(__dirname + '/../..');
const PORT = process.argv.length <= 2 ? 8080 : process.argv[2];
const SUBSERVER_PORT = PORT + 1;

var app = express();
var server = http.Server(app);


nunjucks.configure('views', {
	autoescape: true,
	express: app
});

app.set('views', './views')
app.set('view engine', 'nunjucks');

app.get('/', (req, res) => {
	res.render('index.html', {wsPort: SUBSERVER_PORT});
});

app.use('/static', express.static(ROOT_DIR + '/static'));

server.listen(8080, () => {
	var host = server.address().address;
	var port = server.address().port;

	console.log('Listening on %s:%s', host, port);
});

console.log('starting subserver');
var subserver = child_process.spawn('python', [path.normalize(ROOT_DIR + '/src/py/main.py'), SUBSERVER_PORT]);

subserver.stdout.on('data', function(data) {
	console.log('subserver: ' + data);
});

subserver.stderr.on('data', function(data) {
	console.log('subserver stderr: ' + data);
});

subserver.on('close', (code) => {
	console.log('Subserver closed unexpectedly with code ' + code);
});

process.on('exit', (code) => {
	subserver.kill('SIGINT');
});