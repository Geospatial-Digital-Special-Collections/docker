# Start from an official Python base image.
FROM python:3.14.5

## install dependencies
#RUN apk add --no-cache g++ make cmake git python3-dev py3-pip
RUN apt-get update && apt-get install -y --no-install-recommends \
  g++ \
  libjpeg-dev \
  zlib1g-dev \
  libpng-dev \
  libtiff-dev \
  && rm -rf /var/lib/apt/lists/*

# Create a system user and group named 'gdsc'
# RUN addgroup -S gdsc && adduser -S gdsc -G gdsc
RUN groupadd -g 1000 gdsc && \
    useradd -u 1000 -g gdsc -m -s /bin/bash gdsc
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
RUN pip install --upgrade pip
RUN pip install --upgrade -r requirements.txt

ENTRYPOINT ["./entrypoint.sh"]
# CMD ["nohup", "python", "./gdsc.py", "&"]
# CMD ["uvicorn", "gdsc:app", "--host", "0.0.0.0", "--port", "5150"]