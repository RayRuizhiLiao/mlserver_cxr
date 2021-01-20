FROM rayruizhiliao/mlmodel_cxr_edema:latest

MAINTAINER Ray Liao <ruizhi@mit.edu>

RUN apt-get update && apt-get install -y --no-install-recommends \ 
        dcm2niix \
        gnupg \
        pigz \
        unixodbc-dev \
        ffmpeg \
        libsm6 \
        libxext6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/mlserver

RUN pip3 install --upgrade pip

COPY requirements.txt /opt/mlserver
RUN pip3 install --no-cache-dir -r /opt/mlserver/requirements.txt

COPY . /opt/mlserver
WORKDIR /opt/mlserver
ENV PYTHONPATH=/opt/mlserver:$PYTHONPATH

RUN chmod +x /opt/mlserver/main.py

RUN mkdir -p /images/

ENTRYPOINT ["/opt/mlserver/main.py"]
