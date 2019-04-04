
FROM ubuntu:18.04

# Add Tini
ENV TINI_VERSION v0.18.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    wget curl

ENV PATH "/opt/anaconda3/bin:${PATH}"
RUN echo "PATH=\"/opt/anaconda3/bin:\$PATH\"" >> /etc/bash.bashrc

COPY include/Miniconda3-latest-Linux-x86_64.sh /tmp/
RUN chmod +x /tmp/Miniconda3-latest-Linux-x86_64.sh && \
    tmp/Miniconda3-latest-Linux-x86_64.sh -b -p /opt/anaconda3 && \
    rm /tmp/Miniconda3-latest-Linux-x86_64.sh

RUN conda update -n base conda && pip install --upgrade pip
RUN conda install -c conda-forge protobuf numpy onnx

COPY include/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY include/modelserver.py /home/modelserver.py

ARG model
COPY models/$model/model.onnx /home/model/model.onnx
COPY models/$model/label.p /home/model/labels.p

ENTRYPOINT ["/tini", "--"]
CMD ["python", "/home/modelserver.py"]