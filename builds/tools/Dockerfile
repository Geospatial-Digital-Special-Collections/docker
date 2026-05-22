# Start from an official Python base image.
FROM python:3.15-rc-trixie

# Create a system user and group named 'gdsc'
RUN groupadd -r gdsc && useradd -r -g gdsc gdsc
RUN mkdir -p /home/gdsc && chown -R gdsc:gdsc /home/gdsc

# Set the current working directory to /gdsc.
WORKDIR /gdsc

# copy the flask app and support files
COPY ./builds/tools ./
COPY --chmod=0755 ./builds/tools/entrypoint.sh ./entrypoint.sh

# set user
RUN chown -R gdsc:gdsc ./
USER gdsc

# set up the python environment
RUN pip install --upgrade -r requirements.txt

ENTRYPOINT ["./entrypoint.sh"]
# CMD ["nohup", "python", "./gdsc.py", "&"]
# CMD ["uvicorn", "gdsc:app", "--host", "0.0.0.0", "--port", "5150"]