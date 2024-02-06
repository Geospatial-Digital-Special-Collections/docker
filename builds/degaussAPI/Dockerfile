# Start from an official Python base image.
FROM python:3.9.16-alpine3.17

# Set the current working directory to /code.
WORKDIR /code

# set up the python environment
COPY ./builds/degaussAPI/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# make some placeholders for needed config files
RUN mkdir -p /code/kubernetes/pki && \
    mkdir -p /code/kubernetes/secrets

# copy all config files
COPY ./config/kubernetes/postgis-secret.yaml /code/kubernetes/secrets/
COPY ./config/pki /code/kubernetes/pki
COPY ./config/kubernetes/gdsc-controller-token.yaml /code/kubernetes/secrets/

# copy the app and start it running
COPY ./builds/degaussAPI/degauss.py /code/
CMD ["uvicorn", "degauss:app", "--host", "0.0.0.0", "--port", "8000"]
