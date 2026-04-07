# Start from an official Python base image.
FROM python:3.15-rc-trixie

# Set the current working directory to /gdsc.
WORKDIR /gdsc

# set up the python environment
COPY ./builds/tools/requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the app and start it running
COPY ./builds/tools ./
# CMD ["nohup", "python", "./gdsc.py", "&"]
# CMD ["uvicorn", "gdsc:app", "--host", "0.0.0.0", "--port", "5000"]