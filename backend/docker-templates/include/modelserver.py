import onnxruntime as rt
from PIL import Image
from flask import Flask, request, Response
import numpy as np

app = Flask(__name__)

sess = rt.InferenceSession("../models/vgg19/model.onnx")

input_shape = sess.get_inputs()[0].shape[1:]
output_shape = sess.get_outputs()[0].shape[-1]
print(input_shape, output_shape)


def preprocess_img(image):
    if input_shape[0] == 1:
        img = image.convert("L")
    elif input_shape[0] == 3:
        img = image.convert("RGB")

        b, g, r = img.split()
        img = Image.merge("RGB", (r, g, b))
    else:
        raise AttributeError("Invalid number of image channels for model input layer")

    img = img.resize((input_shape[1], input_shape[2]))
    img_array = np.array(img).astype('float32')

    print(img_array.shape)
    print(img_array.min(), img_array.max())

    img_array = img_array.reshape([input_shape[0], input_shape[1], input_shape[2]])

    if input_shape[0] == 1:
        img_array /= 255
    elif input_shape[0] == 3:
        # img_array = img_array[::-1, ...]

        mean = [103.939, 116.779, 123.68]

        img_array[0, :, :] -= mean[0]
        img_array[1, :, :] -= mean[1]
        img_array[2, :, :] -= mean[2]

    img_array = img_array.reshape([1, input_shape[0], input_shape[1], input_shape[2]])
    print(img_array.shape)
    print(img_array.min(), img_array.max())

    return img_array


@app.route('/get_prediction', methods=['POST'])
def get_prediction():
    req = request
    img = Image.open(req.files['file'])
    img_array = preprocess_img(img)

    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name

    print(img_array.shape)
    print(input_shape)

    pred = sess.run([label_name], {input_name: img_array})[0]
    print(pred.shape)
    print(pred.argmax(axis=1)[0])


    return ""


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
