# Start from an official Python base image.
FROM python:3.9.16-alpine3.17

# copy the init script
COPY --chmod=0500 ./init.sh /docker-entrypoint-initdb.d

# Set the current working directory to /ohdsi.
WORKDIR /ohdsi

# set up the python environment
COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the app and start it running
COPY ./ohdsi.py ./
COPY ./static ./static
COPY ./templates ./templates
CMD ["sleep","infinity"]
# CMD ["nohup", "python", "./ohdsi.py", "&"]
# CMD ["uvicorn", "ohdsi:app", "--host", "0.0.0.0", "--port", "5000"]