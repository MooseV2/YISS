const submitForm = (e) => {
    e.preventDefault();
    let formData = new FormData(contentForm);
    formData.append("onnx", fileOnnx.files[0]);
    formData.append("thumbnail", fileThumbnail.files[0]);
    formData.append("demo", fileDemo.files[0]);
    console.log("Uploading....");

    // Do file upload
    const url = '/upload';
    fetch(url, {
        method: 'POST',
        body: formData
    })
        .then((result) => {
            if (result.status == 200) {
                result.text()
                    .then( (text) => {
                        if (text == 'SUCCESS') {
                            console.log(`Upload succeeded: ${text}`);
                            setState(contentForm, "success");
                        } else {
                            console.log(`Upload failed: ${text}`);
                            setState(contentForm, "error");
                        }
                    })
                    .catch((e) => console.log(`Text error ${e}`));
            } else {
                console.log(`Upload failed: ${result.status}`);
                setState(contentForm, "error");
            }

        })
        .catch((e) => {
            console.log(`Upload failed: ${e}`);
            setState(contentForm, "error");
        });
}

const setState = (element, state) => {
    element.classList.remove("error");
    element.classList.remove("warning");
    element.classList.remove("success");
    element.classList.add(state);
}

const fileSelectHandler = (e, textfield) => {
    let files = e.target.files || e.dataTransfer.files;
    if (files.length > 0) {
        const fileText = document.getElementById(textfield);
        fileText.innerText = `${files[0].name} - ${files[0].size} bytes`
    }
}


const contentForm = document.getElementById("content-form");
const fileOnnx = document.getElementById("file-onnx");
const fileThumbnail = document.getElementById("file-thumbnail");
const fileDemo = document.getElementById("file-demo");
// contentForm.addEventListener("submit", submitForm, false);
fileOnnx.addEventListener("change", (event) => fileSelectHandler(event, "onnx-name"), false);
fileThumbnail.addEventListener("change", (event) => fileSelectHandler(event, "thumb-name"), false);
fileDemo.addEventListener("change", (event) => fileSelectHandler(event, "demo-name"), false);
