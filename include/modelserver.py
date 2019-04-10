import pickle

import numpy as np
import onnxruntime as rt
from PIL import Image
from flask import Flask, request

# initiate flask
app = Flask(__name__)

# load onnx model
sess = rt.InferenceSession("/home/model/model.onnx")

# load model labels
with open("/home/model/labels.p", "rb") as f:
    labels = pickle.load(f)

# save input and output shapes
input_shape = sess.get_inputs()[0].shape[1:]
output_shape = sess.get_outputs()[0].shape[-1]
print(input_shape, output_shape)


def preprocess_img(image):
    """Processes a given image

    :param image: (PIL Image) The queried image
    :return: (Numpy Array) preprocessed image
    """
    # Check if model requires grayscale or RGB
    if input_shape[0] == 1:
        img = image.convert("L")
    elif input_shape[0] == 3:
        img = image.convert("RGB")
    else:
        raise AttributeError("Invalid number of image channels for model input layer")

    # resize image to relevant shape
    img = img.resize((input_shape[1], input_shape[2]))
    img_array = np.array(img).astype('float32')

    print(img_array.shape)
    print(img_array.min(), img_array.max())

    # reshape img to order expected by model
    img_array = img_array.reshape([input_shape[0], input_shape[1], input_shape[2]])

    # pixel scaling for grayscale input
    if input_shape[0] == 1:
        img_array /= 255 if input_shape[1] == 28 else 1

    # pixel scaling for RGB input (WIP)
    elif input_shape[0] == 3:
        print(img_array.ndim)
        img_array = img_array[::-1, ...]
        mean = [103.939, 116.779, 123.68]

        img_array[0, :, :] -= mean[0]
        img_array[1, :, :] -= mean[1]
        img_array[2, :, :] -= mean[2]

    # set batch size as 1
    img_array = img_array.reshape([1, input_shape[0], input_shape[1], input_shape[2]])
    print(img_array.shape)
    print(img_array.min(), img_array.max())

    return img_array


@app.route('/get_prediction', methods=['POST'])
def get_prediction():
    """ Endpoint exposed by flask for performing inference

    :return: (String) Predicted Label
    """

    # retrieve image from request and preprocess it
    req = request
    img = Image.open(req.files['file'])
    img_array = preprocess_img(img)

    # get input layers of Model
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name

    print(img_array.shape)
    print(input_shape)

    # Run inference
    pred = sess.run([label_name], {input_name: img_array})[0]
    print(pred.shape)

    # Get class and relevant class label
    index = pred.argmax(axis=1)[0]
    try:
        return labels[index]
    except IndexError:
        return "Unknown"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
