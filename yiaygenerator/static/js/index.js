'use strict';


// function submit(url) {
	// const sock = new WebSocket(f.action.replace(/^http(s)?:\/\//, 'ws$1://'));
	// const sock = new WebSocket(`ws://${window.location.host}/request/?question=a&hashtag=b`);
	//
	// sock.onopen = function (event) {
	// 	console.log(event);
	// };
	// sock.onmessage = function (msg) {
	// 	console.log(msg);
	// };
	//
	
	//console.log(url);
// }


import m from 'mithril';

window.onload = () => m.render(document.body, 'hello world');

// window.onload = function () {
// 	console.log('window');
// 	document.forms[0].onsubmit = function () {
// 		console.log('lol');
// 		return false;
// 	};
// };


	// <form action="/request/">
	// 	<label for="question">Question</label>
	// 	<input type="text" name="question" id="question" />
	// 	<br />
	// 	<label for="hashtag">Hashtag</label>
	// 	<input type="text" name="hashtag" id="hashtag" />
	// 	<br />
	// 	<input type="submit" value="Let's a go!" />
	// </form>
