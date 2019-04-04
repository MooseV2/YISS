import os
import pickle
import shelve
import subprocess
from uuid import uuid4

import docker
import requests
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from flask_uuid import FlaskUUID

app = Flask(__name__)
FlaskUUID(app)


docker_client = docker.from_env()

ip_dict = None
if os.path.isfile('proxy.p'):
    with open('proxy.p', 'rb') as proxy_file:
        ip_dict = pickle.load(proxy_file)
else:
    ip_dict = {}


@app.route('/')
def index():
    """
    Renders the default page for uploading images
    :return: index.html template
    """
    with shelve.open("persistent_data") as db:
        model_info = {k:v["name"] for (k,v) in db.items()}

    return render_template('index.html', gallery=model_info)


@app.route('/images/<path:path>')
def send_image(path):
    return send_from_directory('images', path)


@app.route('/models/<uuid>/', methods=['GET', 'POST'])
def model(uuid):
    """
    Renders the results page with the analysis JSON data
    :param uuid: The UUID of the results page
    :return: model.html template, or 404.html on error
    """
    uuid = str(uuid)
    url = "yourinference.ml/models"
    # try:
    post = request.method == 'POST'

    if post:
        img_file = request.files['file']
    else:
        img_file = None
    
    name, desc, output = load_result(uuid, post, img_file=img_file)
    # except: # UUID wasn't found, throw 404
    #     return '404 :('
    #     # TODO: 404.html
    #     # return render_template('404.html')

    if not post:
        return render_template('model.html', 
                                url=url,
                                name=name, 
                                description=desc, 
                                output=output, 
                                uuid=uuid)
    else:
        return output


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
    uuid = str(uuid4())[:8]
    
    thumb_path = os.path.join('images', f'thumb-{uuid}.jpg')
    thumb.save(thumb_path)
    
    demo_path = os.path.join('images', f'demo-{uuid}.jpg')
    demo.save(demo_path)

    # Create directory for model
    model_dir = os.path.join('models', uuid)
    os.mkdir(model_dir)
    model_path = os.path.join(model_dir, 'model.onnx')
    onnx.save(model_path)

    with shelve.open("persistent_data") as db:
        db[uuid] = {
            "onnx": model_path,
            "name": name,
            "description": desc,
            "thumbnail": thumb_path,
            "demo": demo_path
        }

    label_path = os.path.join(model_dir, 'label.p')
    label_list = labels.split(', ')

    with open(label_path, 'wb') as label_file:
        pickle.dump(label_list, label_file)

    docker_client.images.build(path=".", tag=uuid, buildargs={'model': uuid})
    docker_client.containers.run(uuid, detach=True, name=uuid)

    ip = subprocess.check_output(
        ["docker", "inspect", "-f", "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'", str(uuid)],
        shell=False
    )

    ip = ip.decode('utf-8').rstrip()
    print(ip)
    ip_dict[uuid] = ip

    with open("proxy.p", 'wb') as _proxy_file:
        pickle.dump(ip_dict, _proxy_file)

    # TODO: Instantiate model container
    return redirect(url_for('index'))


def load_result(uuid, post, img_file=None):
    """ Given a UUID, returns the corresponding result JSON.
        Returns: JSON on success, None on failure
    """

    if type(uuid) is bytes:
        uuid = uuid.decode('utf-8')

    with shelve.open("persistent_data") as db:
        model = db[uuid]
        name = model["name"]
        desc = model["description"]
        demo = model["demo"]

    if not post:
        img_file = open(demo, "rb")

    model_ip = ip_dict[uuid]
    model_endpoint = "http://{}:5001/get_prediction".format(model_ip[1:-1])
    print(model_endpoint)

    r = requests.post(model_endpoint, files={'file': img_file}).text
    print(r)

    return (name, desc, r)

    # TODO


if __name__ == '__main__':
    app.run(host='yourinference.ml', port=80)  # Start the server
