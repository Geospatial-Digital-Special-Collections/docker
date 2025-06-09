# Start from an official Python base image.
FROM python:3.9.16-alpine3.17

# Set the current working directory to /gdsc.
WORKDIR /gdsc

# set up the python environment
COPY ./builds/repository/requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the app and start it running
COPY ./builds/repository ./
# CMD ["nohup", "python", "./gdsc.py", "&"]
# CMD ["uvicorn", "gdsc:app", "--host", "0.0.0.0", "--port", "5000"]