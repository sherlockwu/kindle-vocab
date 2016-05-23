// static
var dict;             // map words to defs
var words;            // words user wants to practice
var quiz_words = [];  // subset of "words" for which we have defs
var fbid = "0";

// per round
var cur_words = [];   // four words used to quiz user
var correct_word;

function status(val) {
    $("#status").html(val);
}

function lambda(data, success) {
    data["fbid"] = fbid;
    $.ajax({
	url: "https://4pcltxpssg.execute-api.us-east-1.amazonaws.com/prod/kindle-vocab",
	type: "POST",
	data: JSON.stringify(data),
	contentType: "application/json",
	success: function(data) {
	    if (typeof data  === "object" && "errorType" in data) {
		status("Lambda " + data["errorType"] + ": " + data["errorMessage"]);
	    } else {
		success(data);
	    }
	},
	error: function(xhr, ajaxOptions, thrownError) {
	    status("could not reach backend servers");
	    console.log(thrownError);
	}
    });
}

function login() {
    FB.login(function(response) {
	if (response.authResponse) {
	    fbid = response.authResponse.accessToken;
	    lambda({"op":"fetch"}, load_words);
	    status("fetching your words");
	} else {
	    status('could not sign you in');
	}
    });
}

function demo() {
    fbid = "0";
    lambda({"op":"fetch"}, load_words);
    status("fetching your words");
}

function upload() {
    file = $("#file")[0];

    status("reading file");
    if (file.value == "") {
	status("Select one or more files.");
    } else {
	var reader = new FileReader();
	reader.onload = function(event) {
	    status("uploading file");
	    cmd = {"op":"upload", "db":btoa(event.target.result)};
	    lambda(cmd, function(data) {
		status(data);
		lambda({"op":"fetch"}, load_words);
		status("fetching your words");
	    });
	};
	reader.onerror = function(event) {
	    status("failed to read file");
	}
	reader.readAsBinaryString(file.files[0]);
    }
}

function show_question(answer) {
    question_text = dict[correct_word] + '<br/>';
    question_text += '<hr/>';
    for (var i=0; i<cur_words.length; i++) {
	question_text += '('+(i+1)+') ';
	if (cur_words[i] == answer) {
	    question_text += '<b>' + cur_words[i] + '</b>';
	} else {
	    question_text += cur_words[i];
	}
	question_text += '<br/>\n';
    }

    if (answer != undefined) {
	if (answer == correct_word) {
	    question_text += '<br/>';
	    question_text += 'Nice!';
	    setTimeout(quiz, 1000);
	} else {
	    question_text += '<br/>';
	    question_text += 'Wrong!';
	    $("#answer").val('');
	}
    }
    
    $("#question").html(question_text);
}

function answer() {
    show_question(cur_words[parseInt($("#answer").val()) - 1]);
}

function quiz() {
    if (quiz_words.length == 0) {
	status("No words uploaded yet");
	$("#question").html("Upload some words...");
	return;
    }
    
    q = new Set();
    while (q.size < Math.min(4, quiz_words.length)) {
	word = quiz_words[Math.floor(Math.random()*quiz_words.length)];
	q.add(word);
    }
    cur_words = [];
    q.forEach(function(val){
	cur_words.push(val);
    });

    correct_word = cur_words[Math.floor(Math.random()*cur_words.length)];
    show_question();
    $("#answer").val('');
}

// step 1
function load_defs(data) {
    dict = data;
    lambda({"op":"fetch"}, load_words);
    status("fetching your words");
}

// step 2
function load_words(data) {
    words = data.words;
    quiz_words = [];
    for (var i = 0; i < words.length; i++) {
	word = words[i].toLowerCase();
	if (word in dict) {
	    quiz_words.push(word);
	}
    }
    status("quizzing you on " + quiz_words.length + " words");
    quiz();
}

function main() {
    FB.init({
	appId: '508032036052362',
	version: 'v2.6'
    });
    dict = null;
    $.getJSON("dict.json", load_defs);
    status("fetching dictionary");
}
