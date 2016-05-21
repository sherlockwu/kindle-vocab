function status(val) {
    $("#status").html(val);
}

function lambda(data, success) {
    $.ajax({
	url: "https://4pcltxpssg.execute-api.us-east-1.amazonaws.com/prod/kindle-vocab",
	type: "POST",
	data: JSON.stringify(data),
	contentType: "application/json",
	success: function(data) {
	    console.log(typeof(data));
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
	    });
	};
	reader.onerror = function(event) {
	    status("failed to read file");
	}
	reader.readAsBinaryString(file.files[0]);
    }
}

function main() {
    dict = null;
    $.getJSON("dict.json", function(data) {
	dict = data;

	cmd = {"op":"fetch"};
	lambda(cmd, function(data) {
	    words = data.words;
	    var hit = 0;
	    var miss = 0;
	    for (var i = 0; i < words.length; i++) {
		word = words[i].toLowerCase();
		console.log(word);
		if (word in dict) {
		    hit += 1;
		} else {
		    miss += 1;
		}
		console.log(dict[word]);
	    }
	    console.log(hit);
	    console.log(miss);
	});
    });
}
