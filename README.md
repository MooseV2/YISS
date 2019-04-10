# YISS
Your Inference Served as a Service - Automatic API frontend for deploying ML models to the cloud

## Steps to deploy

1 - Ensure docker and python 3.7 are installed on the system you wish to host the web server.

2 - Download miniconda from https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh and place it under
the include directory at the root of this repo.

3 - From the root of the repo install the requirements with the following: 
```python
pip install -r requirements.txt
```

4 - If running locally change line 13 and 14 to the following in app.py:
```python
HOST_IP = '0.0.0.0'  # change to url of server if hosting online
HOST_PORT = '8080'  # use port 80 if hosting online
```

5 - Start the server with:
```python
python app.py
```

The MNIST model is a good place to start. The onnx file can be found here:
https://github.com/onnx/models/tree/master/mnist

The dataset for MNIST can be downloaded from https://www.kaggle.com/scolianni/mnistasjpg

Please note that the first model uploaded will take a while to build the container
as the docker images would not be cached.