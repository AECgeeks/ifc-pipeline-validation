

function sendInfo(index = null) {
    console.log(this)
    var property = event.srcElement.id.split('_')[0];
    var modelCode = event.srcElement.id.split('_')[1];
    console.log(modelCode)
    var data = { type: property, val: this.value, code: modelCode};

    fetch("/update_info/" + modelCode, {
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
        ['syntaxlog', 'schemalog', 'mvdlog', 'bsddlog'].forEach((x, i) => {
            var img = document.createElement("img");
            img.src = "/static/icons/" + icons[r["results"][x]] + ".png";
            rows[row_index].cells[i].appendChild(img);
          });

        rows[row_index].cells[8].innerHTML = r["time"];
        rows[row_index].cells[8].style.fontWeight = "bold";
        rows[row_index].cells[8].style.color = "#d9d9d9";
    });

    var repText = document.createElement("a");
    repText.id = "report"
    repText.innerHTML = "View report"
    repText.href = `/report2/${savedModels[i].code}`;
    rows[row_index].cells[toColumnComplete["report"]].appendChild(repText)

    rows[row_index].cells[7].appendChild(repText)

    rows[row_index].cells[7].style.color = "#0070C0";
    rows[row_index].cells[7].style.fontWeight = "bold";
    rows[row_index].cells[7].id = "report"

    var a = document.createElement('a');
    var linkText = document.createTextNode("Download");
    a.appendChild(linkText);
    a.title = "Download";
    a.href = `/download/${savedModels[i].id}`;
    a.style.textDecoration = "none";

    var children = rows[row_index].cells[9].childNodes;
    rows[row_index].cells[9].removeChild(children[0]);
    rows[row_index].cells[9].appendChild(a);

    a.style.color = "inherit";
    rows[row_index].cells[10].innerHTML = '<a href="{{ url_for("index") }}" style ="text-decoration:none;">Delete</a>';

    rows[row_index].cells[9].style.fontWeight = "bold";
    rows[row_index].cells[10].style.fontWeight = "bold";
    rows[row_index].cells[9].style.color = "rgb(105, 125, 239)";
    rows[row_index].cells[10].style.color = "rgb(224, 101, 101)";


}

var table = document.getElementById("saved_models");
var nCols = Object.keys(toColumnComplete).length;
var unsavedConcat = "";
var modelIds = [];
var codeToId = {};
var idToRowIndex = {}


savedModels.forEach((model, i) => {
    var rowIndex = i + 1;
    var row = table.insertRow(rowIndex);
    row.id = model.id;

    for (var col = 0; col < nCols; col++) {
        row.insertCell(col);
    }

    var ifcLogo = document.createElement("IMG");
    ifcLogo.src = "/static/icons/ifc.png";
    row.cells[toColumnComplete["file_format"]].appendChild(ifcLogo);

    row.cells[toColumnComplete["file_format"]].appendChild(ifcLogo);
    row.cells[toColumnComplete["file_name"]].innerHTML = model.filename;
    row.cells[toColumnComplete["file_name"]].style.textAlign = "left";
    row.cells[toColumnComplete["file_name"]].className = "filename";

    var licenseSelect = document.createElement("SELECT");


    var licensTypes = ["private", "CC", "MIT", "GPL", "LGPL"];
    for (const license of licensTypes) {
        var option = document.createElement("option");
        option.text = license;
        licenseSelect.add(option);
    }

    licenseSelect.id = "license_" + model.code;
    licenseSelect.addEventListener("change", sendInfo);
    licenseSelect.value = model.license
    row.cells[toColumnComplete["license"]].appendChild(licenseSelect);

    var hoursInput = document.createElement("INPUT");
    hoursInput.id = "hours_" + model.code
    hoursInput.addEventListener("change", sendInfo);
    hoursInput.value = model.hours;
    hoursInput.style.width = "30px"
    row.cells[toColumnComplete["hours"]].appendChild(hoursInput);

    var detailsInput = document.createElement("INPUT");
    detailsInput.id = "details_" + model.code
    detailsInput.addEventListener("change", sendInfo);
    detailsInput.value = model.details
    row.cells[toColumnComplete["details"]].appendChild(detailsInput);




    if (model.progress == 100) {


        var checks_type = ["syntax", "schema", "mvd", "bsdd", "ids"];
        var icons = { 'v': 'valid', 'w': 'warning', 'i': 'invalid', 'n': 'not' };
        for (var j = 0; j < checks_type.length; j++) {
            var attr = "status_" + checks_type[j];
            var status_result = model[attr];
            var icon = icons[status_result];
            var img = document.createElement("IMG");
            img.src = "/static/icons/" + icon + ".png";
            row.cells[toColumnComplete[checks_type[j]]].appendChild(img);

        }




        var repText = document.createElement("a");
        repText.id = "report"
        repText.innerHTML = "View report"
        repText.href = `/report2/${model.code}`;

        row.cells[toColumnComplete["report"]].appendChild(repText)

        row.cells[toColumnComplete["report"]].style.color = "#0070C0";
        row.cells[toColumnComplete["report"]].style.fontWeight = "bold";
        row.cells[toColumnComplete["report"]].id = "report"

        row.cells[toColumnComplete["date"]].innerHTML = model.date

        var a = document.createElement('a');
        var linkText = document.createTextNode("Download");
        a.appendChild(linkText);
        a.title = "Download";
        a.style.color = "inherit";

        a.href = `/download/${model.id}`;
        a.style.textDecoration = "none";
        row.cells[toColumnComplete["download"]].appendChild(a);


        row.cells[toColumnComplete["delete"]].innerHTML = "Delete";



        row.cells[toColumnComplete["download"]].style.fontWeight = "bold";


        row.cells[toColumnComplete["delete"]].style.fontWeight = "bold";
        row.cells[toColumnComplete["download"]].style.color = "rgb(105, 125, 239)";
        row.cells[toColumnComplete["delete"]].style.color = "rgb(224, 101, 101)";




        row.cells[toColumnComplete["geoms"]].innerHTML = model.number_of_geometries;
        row.cells[toColumnComplete["props"]].innerHTML = model.number_of_properties;


    }

    else {
        console.log("unsaved");
        unsavedConcat += model.code;
        modelIds.push(model.id);

        idToRowIndex[model.id] = rowIndex;

        row.cells[toColumnUncomplete["stop"]].innerHTML = "Stop";

        const newDiv = document.createElement("div");
        newDiv.className = "progress"
        const barDiv = document.createElement("div");
        barDiv.id = "bar" + model.id;
        barDiv.className = "bar";
        newDiv.appendChild(barDiv)
        row.cells[toColumnUncomplete["progress"]].appendChild(newDiv);

        row.cells[toColumnUncomplete["advancement"]].innerHTML = model.progress;
        row.cells[toColumnUncomplete["advancement"]].id = "percentage" + model.id;
        codeToId[model.code] = model.id;


    }
});




const registered = new Set();
function poll(unsavedConcat) {
    fetch("/valprog/" + unsavedConcat).then(function (r) { return r.json(); }).then(function (r) {
        for (var i = 0; i < r.progress.length; i++) {
            var str = unsavedConcat;
            var modelCode = str.match(/.{1,32}/g)
            var id = codeToId[modelCode[i]]
            var percentage = document.getElementById("percentage" + id)
            var bar = document.getElementById("bar" + id)

            var file_row = document.getElementById(id)
            file_row.cells[toColumnUncomplete["geoms"]].innerHTML = r["file_info"][i]["number_of_geometries"]
            file_row.cells[toColumnUncomplete["props"]].innerHTML = r["file_info"][i]["number_of_properties"]

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

