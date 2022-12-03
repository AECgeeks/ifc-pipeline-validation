import React, { useEffect } from "react";
import './Dz.css'
import { FETCH_PATH } from './environment'

function Dz() {

    useEffect(() => {
        window.Dropzone.autoDiscover = false;
        var dz = new window.Dropzone("#ifc_dropzone",
            {
                uploadMultiple: true,
                acceptedFiles: ".ifc, .xml",
                parallelUploads: 100,
                maxFiles: 100,
                maxFilesize: 8 * 1024,
                autoProcessQueue: false,
                addRemoveLinks: true,
            });

        dz.on("addedfile", file => { console.log("new file") });

        dz.on("success", function (file, response) {
            window.location = response.url;
        });

        var submitButton = document.querySelector("#submit");
        submitButton.addEventListener("click", function () {
            dz.processQueue();
        });


    }, []);

    return (
        <div>
            <div className="submit-area" id="ifc_tab">
                <form action={`${FETCH_PATH}/api/`} className="dropzone" id="ifc_dropzone">
                    <div className="dz-message" data-dz-message><span><i className="material-icons"></i> Click or drop files here to upload for validation</span></div>
                </form>
                <button className="submit-button" id="submit">Start validation</button>
            </div>
        </div>
    );

}

export default Dz;