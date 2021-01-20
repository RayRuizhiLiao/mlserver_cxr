# mlserver_cxr

A server that runs a chest radiograph ML model and listens to a port that transfers DICOM images.

Docker image available at: https://hub.docker.com/repository/docker/rayruizhiliao/mlserver_cxr

## Docker image

To build the Docker image, run
```
sudo docker build -t mlserver_cxr .
```

To run the Docker image, run 
```
sudo docker run -it -p 127.0.0.1:11114:11114/tcp --mount type=bind,source=/var/local/,target=/images/ rayruizhiliao/mlserver_cxr:latest
```

You may use ```pynetdicom``` to test this server:
```
python -m pynetdicom storescu 127.0.0.1 11114 ./example_data/2558021a-857a3374-fe220c04-d6bf3dc2-1f789c9e.dcm -d -cx
```
