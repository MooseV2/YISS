from flask import Flask, render_template, request
import os
from uuid import uuid4
import pickle
from threading import Thread
import glob # TODO: Remove after proper gallery retreival
app = Flask(__name__)

@app.route('/')
def index():
    """
    Renders the default page for uploading images
    :return: index.html template
    """
    uuids = [x.split('/')[1] for x in glob.glob('models/*')]
    model_info = {uuid:"name" for uuid in uuids}

    return render_template('index.html', gallery=model_info)


@app.route('/model/<uuid>')
def model(uuid):
    """
    Renders the results page with the analysis JSON data
    :param uuid: The UUID of the results page
    :return: model.html template, or 404.html on error
    """
    result = load_result(uuid)
    if result is None: # UUID wasn't found, throw 404
        return render_template('404.html')

    return render_template('result.html', filename=result["filename"],
                           details=result["exif"],
                           classification=result["labels"],
                           before=result["before"],
                           after=result["after"],
                           timestamp=result["timestamp"])



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Uploads the image from the form data and starts the analysis in a thread
    :return: string 'SUCCESS' on success, 'FAIL' on failure
    """
    # Ensure the user has added a file and email

    if request.method == 'GET':
        return render_template('upload.html')

    try:
        onnx = request.files['onnx']
        thumb = request.files['thumbnail']
        demo = request.files['demo']
        desc = request.form['description']
        name = request.form['name']
        labels = request.form['labels']
    except:
        import traceback
        return traceback.print_exc()

    # Otherwise, save the file
    new_filename = str(uuid4())
    
    thumb_path = os.path.join('images', f'thumb-{new_filename}.jpg')
    thumb.save(thumb_path)
    
    demo_path = os.path.join('images', f'demo-{new_filename}.jpg')
    demo.save(demo_path)

    # Create directory for model
    model_dir = os.path.join('models', new_filename)
    os.mkdir(model_dir)
    model_path = os.path.join(model_dir, 'model.onnx')
    onnx.save(model_path)

    label_path = os.path.join(model_dir, 'label.p')
    label_list = labels.split(', ')

    with open(label_path, 'wb') as label_file:
        pickle.dump(label_list, label_file)
    
    # TODO: Instantiate model container
    return f"""
        UUID:\t{new_filename}
        <br>Thumbnail:\t{thumb_path}
        <br>Demo:\t{demo_path}
        <br>Model:\t{model_path}
        <br>Name:\t{name}
        <br>
        <br>-------
        <br>Labels
        <br>-------
        <br>{labels}
        <br>-------
        <br>Description
        <br>-------
        <br>{desc}
    """

def load_result(uuid, retry=False):
    """ Given a UUID, returns the corresponding result JSON.
        Returns: JSON on success, None on failure
    """
    pass # TODO

if __name__ == '__main__':
    app.run() # Start the server