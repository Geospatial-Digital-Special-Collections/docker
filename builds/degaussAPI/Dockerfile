# Start from an official Python base image.
FROM python:3.9.16-alpine3.17

# Set the current working directory to /code.
WORKDIR /code

# set up the python environment
COPY ./docker/degaussAPI/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# make some placeholders for needed config files
RUN mkdir -p /code/kubernetes/pki && \
    mkdir -p /code/kubernetes/secrets

# copy all config files
COPY ./kubernetes/secrets/postgis-secret.yaml /code/kubernetes/secrets/
COPY ./kubernetes/pki /code/kubernetes/pki
COPY ./kubernetes/secrets/gdsc-controller-token.yaml /code/kubernetes/secrets/

# copy the app and start it running
COPY ./docker/degaussAPI/degauss.py /code/
CMD ["uvicorn", "degauss:app", "--host", "0.0.0.0", "--port", "8000"]
