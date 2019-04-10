import os
import pickle
import shelve
import subprocess
from uuid import uuid4

import docker
import requests
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from flask_uuid import FlaskUUID

# Change following to '0.0.0.0' and '8080' if running locally
HOST_IP = 'yourinference.ml'
HOST_PORT = '80'

# initiate flask app
app = Flask(__name__)
FlaskUUID(app)

# connect to docker client
docker_client = docker.from_env()

# initialize ip lookup
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
    # open shelve db
    with shelve.open("persistent_data") as db:
        model_info = {k:v["name"] for (k,v) in db.items()}

    # render gallery with existing models
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

    # get provided UUID
    uuid = str(uuid)

    # prepare URL
    url = "{}:{}/models".format(HOST_IP, HOST_PORT)

    # if POST, send file to relevant container
    try:
        post = request.method == 'POST'

        if post:
            img_file = request.files['file']
        else:
            img_file = None

        # Get result of inference from relevant model
        name, desc, output = load_result(uuid, post, img_file=img_file)
    except Exception as e:  # UUID wasn't found, throw 404
        return '404 :('

    # if not post, then Model page is being requested.
    if not post:
        return render_template('model.html', 
                                url=url,
                                name=name, 
                                description=desc, 
                                output=output, 
                                uuid=uuid)

    # if POST, then only return class label
    else:
        return output


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """ Uploads the model and metadata from the form data, creates the new container.

    :return: web view
    """

    # show model upload page if GET request
    if request.method == 'GET':
        return render_template('upload.html')

    # grab data from request
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

    # generate random uuid
    uuid = str(uuid4())[:8]

    # save thumbnail and demo image under images folder
    thumb_path = os.path.join('images', f'thumb-{uuid}.jpg')
    thumb.save(thumb_path)
    demo_path = os.path.join('images', f'demo-{uuid}.jpg')
    demo.save(demo_path)

    # Create directory for model and save it
    model_dir = os.path.join('models', uuid)
    os.mkdir(model_dir)
    model_path = os.path.join(model_dir, 'model.onnx')
    onnx.save(model_path)

    # store paths and metadata
    with shelve.open("persistent_data") as db:
        db[uuid] = {
            "onnx": model_path,
            "name": name,
            "description": desc,
            "thumbnail": thumb_path,
            "demo": demo_path
        }

    # save label pickle file under model dir
    label_path = os.path.join(model_dir, 'label.p')
    label_list = labels.split(', ')
    with open(label_path, 'wb') as label_file:
        pickle.dump(label_list, label_file)

    # build and start container
    docker_client.images.build(path=".", tag=uuid, buildargs={'model': uuid})
    docker_client.containers.run(uuid, detach=True, name=uuid)

    # check ip of running container and save it in lookup
    ip = subprocess.check_output(
        ["docker", "inspect", "-f", "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'", str(uuid)],
        shell=False
    )
    ip = ip.decode('utf-8').rstrip()
    print(ip)
    ip_dict[uuid] = ip

    # save proxy file
    with open("proxy.p", 'wb') as _proxy_file:
        pickle.dump(ip_dict, _proxy_file)

    # return index if successful
    return redirect(url_for('index'))


def load_result(uuid, post, img_file=None):
    """ Given a UUID, returns the corresponding result JSON.
        Returns: JSON on success, None on failure
    """

    # extract string if bytes
    if type(uuid) is bytes:
        uuid = uuid.decode('utf-8')

    # get metadata from db
    with shelve.open("persistent_data") as db:
        model = db[uuid]
        name = model["name"]
        desc = model["description"]
        demo = model["demo"]

    # if viewing model page, get demo image
    if not post:
        img_file = open(demo, "rb")

    # get ip of relevant container
    model_ip = ip_dict[uuid]
    model_endpoint = "http://{}:5001/get_prediction".format(model_ip[1:-1])
    print(model_endpoint)

    # get classification
    r = requests.post(model_endpoint, files={'file': img_file}).text
    print(r)

    # return result
    return (name, desc, r)


if __name__ == '__main__':
    app.run(host=HOST_IP, port=int(HOST_PORT))  # Start the server
