



function sendInfo(index = null) {
    //debugger;
    console.log(this)

    var property = event.srcElement.id.split('_')[0];
    var modelCode = event.srcElement.id.split('_')[1];
   
    var data = { type: property, val: this.value, n: i };

    

    fetch("/updateinfo2/" + modelCode, {
        method: "POST",
        body: JSON.stringify(data)
    }).then(function (r) { return r.json(); }).then(function (r) {
        console.log(r);
    })

}


var icons = { 'v': 'valid', 'w': 'warning', 'i': 'invalid', 'n': 'not' };
function completeTable(i) {
    var table = document.getElementById("saved_models");
    var row_index = idToRowIndex[modelIds[i]];
    var rows = table.rows;

    fetch("/reslogs/" + i + "/" + unsavedConcat).then(function (r) { return r.json(); }).then(function (r) {

        console.log(r["results"]['bsddlog']);

        var syntaxImg = document.createElement("img");
        syntaxImg.src = "/static/icons/" + icons[r["results"]['syntaxlog']] + ".png";

        var schemaImg = document.createElement("img");
        schemaImg.src = "/static/icons/" + icons[r["results"]['schemalog']] + ".png";

        var MVDImg = document.createElement("img");
        MVDImg.src = "/static/icons/" + icons[r["results"]['mvdlog']] + ".png";

        var bsddImg = document.createElement("img");
        bsddImg.src = "/static/icons/" + icons[r["results"]['bsddlog']] + ".png";

        var idsImg = document.createElement("img");
        idsImg.src = "/static/icons/" + icons[r["results"]['idslog']] + ".png";

        rows[row_index].cells[0].appendChild(syntaxImg);
        rows[row_index].cells[1].appendChild(schemaImg);
        rows[row_index].cells[2].appendChild(MVDImg);
        rows[row_index].cells[3].appendChild(bsddImg);
        rows[row_index].cells[4].appendChild(idsImg);

        rows[row_index].cells[8].innerHTML = r["time"];
        rows[row_index].cells[8].style.fontWeight = "bold";
        rows[row_index].cells[8].style.color = "#d9d9d9";


    });


    var repText = document.createElement("a");
    repText.id = "report"
    repText.style.textDecoration = "none";
    repText.innerHTML = "View report"
    var fn = rows[row_index].cells[6].innerHTML;
    var st = window.location.href;

    var baseUrl = st.split('/')[2];
    var url = "/report/" + i + "/" + unsavedConcat + "/" + fn;

    repText.href = url;
    rows[row_index].cells[7].appendChild(repText)

    rows[row_index].cells[7].style.color = "#0070C0";
    rows[row_index].cells[7].style.fontWeight = "bold";
    rows[row_index].cells[7].id = "report"

    rows[row_index].cells[9].innerHTML = '<a href="{{ url_for("index") }}" style ="text-decoration:none;">Download</a>';
    rows[row_index].cells[10].innerHTML = '<a href="{{ url_for("index") }}" style ="text-decoration:none;">Delete</a>';

    rows[row_index].cells[9].style.fontWeight = "bold";
    rows[row_index].cells[10].style.fontWeight = "bold";
    rows[row_index].cells[9].style.color = "rgb(105, 125, 239)";
    rows[row_index].cells[10].style.color = "rgb(224, 101, 101)";


    

    //License
    var values = ["private", "CC", "MIT", "GPL"];

    // var select = document.createElement("select");
    // select.name = "licenses";
    // select.id = "licenses"
    var select = document.getElementById("licenses");
    //select.addEventListener("change", sendInfo);

    //Production hours
    var hoursInputBox = document.getElementById("hours");
    //hoursInputBox.addEventListener("change", sendInfo);


    //Additional details
    var detailsInputBox = document.getElementById("details");
    //detailsInputBox.addEventListener("change", sendInfo);

}

var table = document.getElementById("saved_models");
var nCols = Object.keys(toColumnComplete).length;
var unsavedConcat = "";
var modelIds = [];
var codeToId = {};
var idToRowIndex = {}


for (var i = 0; i < savedModels.length; i++) {

    var rowIndex = i + 1;
    var row = table.insertRow(rowIndex);
    row.id = savedModels[i].id;

    for (var col = 0; col < nCols; col++) {
        row.insertCell(col);
    }
    var ifcLogo = document.createElement("IMG");
    ifcLogo.src = "/static/icons/ifc.png";
    row.cells[toColumnComplete["file_format"]].appendChild(ifcLogo);

    row.cells[toColumnComplete["file_format"]].appendChild(ifcLogo);
    row.cells[toColumnComplete["file_name"]].innerHTML = savedModels[i].filename;

    var licenseSelect = document.createElement("SELECT");
        

    var licensTypes = ["private", "CC", "MIT", "GPL", "LGPL"];
    for (const license of licensTypes) {
        var option = document.createElement("option");
        option.text = license;
        licenseSelect.add(option);
    }

    licenseSelect.id = "license_"+savedModels[i].code;
    licenseSelect.addEventListener("change", sendInfo);
    licenseSelect.value = savedModels[i].license
    row.cells[toColumnComplete["license"]].appendChild(licenseSelect);

    var hoursInput = document.createElement("INPUT");
    hoursInput.id = "hours_"+savedModels[i].code
    hoursInput.addEventListener("change", sendInfo);
    hoursInput.value = savedModels[i].hours;
    row.cells[toColumnComplete["hours"]].appendChild(hoursInput);

    var detailsInput = document.createElement("INPUT");
    detailsInput.id = "details_"+savedModels[i].code
    detailsInput.addEventListener("change", sendInfo);
    detailsInput.value = savedModels[i].details        
    row.cells[toColumnComplete["details"]].appendChild(detailsInput);




    if (savedModels[i].progress == 100) {


        row.cells[toColumnComplete["report"]].innerHTML = "View report";
        row.cells[toColumnComplete["date"]].innerHTML = savedModels[i].date

        
        

        var a = document.createElement('a');
        var linkText = document.createTextNode("Download");
        a.appendChild(linkText);
        a.title = "Download";

        var splittedLocation = window.location.href.split("/");
        var domain = splittedLocation[0] +"/"+ splittedLocation[1] + splittedLocation[2]
        a.href = "/download/" +  savedModels[i].id.toString();
        row.cells[toColumnComplete["download"]].appendChild(a);

        
        row.cells[toColumnComplete["delete"]].innerHTML = "Delete";

        row.cells[toColumnComplete["geoms"]].innerHTML = savedModels[i].number_of_geometries;
        row.cells[toColumnComplete["props"]].innerHTML = savedModels[i].number_of_properties;


    }

    else {
        console.log("unsaved");
        unsavedConcat += savedModels[i].code;
        modelIds.push(savedModels[i].id);

        idToRowIndex[savedModels[i].id] = rowIndex;

        row.cells[toColumnUncomplete["stop"]].innerHTML = "Stop";

        const newDiv = document.createElement("div");
        newDiv.className = "progress"
        const barDiv = document.createElement("div");
        barDiv.id = "bar" + savedModels[i].id;
        barDiv.className = "bar";
        newDiv.appendChild(barDiv)
        row.cells[toColumnUncomplete["progress"]].appendChild(newDiv);

        row.cells[toColumnUncomplete["advancement"]].innerHTML = savedModels[i].progress;
        row.cells[toColumnUncomplete["advancement"]].id = "percentage" + savedModels[i].id;
        codeToId[savedModels[i].code] = savedModels[i].id;


    }

}


const registered = new Set();
function poll(unsavedConcat) {
    fetch("/valprog/" + unsavedConcat).then(function (r) { return r.json(); }).then(function (r) {
        for (var i = 0; i < r.progress.length; i++) {
            var str = unsavedConcat;
            var modelCode = str.match(/.{1,32}/g)
            var id = codeToId[modelCode[i]]
            var percentage = document.getElementById("percentage" + id)
            var bar = document.getElementById("bar" + id)


            if (r.progress[i] === 100) {

                if (!registered.has(i)) {

                    registered.add(i);

                    bar.style.width = 100 * 2 + 'px';
                    percentage.innerHTML = "100%"
                    completeTable(i);

                }

            } else {
                var p = r.progress[i];
                if (p < 0) {
                    percentage.innerHTML = "<i>in queue</i>";
                    p = 0
                } else {
                    percentage.innerHTML = p + "%";
                }
                bar.style.width = p * 2 + 'px';

            }

        }

        setTimeout(poll(unsavedConcat), 1000);

    });

}


if (unsavedConcat) {
    console.log("/valprog/" + unsavedConcat);
    poll(unsavedConcat);

}