function status(val) {
    $("#status").text(val);
}

function upload() {
    file = $("#file")[0];
    status("reading file");
    if (file.value == "") {
	status("Select one or more files.");
    } else {
	var reader = new FileReader();
	reader.onload = function(event) {
	    status(event.target.result);
	};
	reader.onerror = function(event) {
	    status("failed to read file");
	}
	reader.readAsText(file.files[0]);
    }
}

function main() {
    status("Please upload a file");
}
