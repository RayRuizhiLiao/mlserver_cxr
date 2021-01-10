FROM continuumio/miniconda3

# Create the environment:
COPY environment.yml .
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "docker_bidmc", "/bin/bash", "-c"]

# The code to run when container is started:
COPY main.py .
ENTRYPOINT ["conda", "run", "-n", "docker_bidmc", "python", "main.py"]