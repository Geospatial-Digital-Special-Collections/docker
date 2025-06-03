FROM python:3.10-alpine

ENV USER=gdsc
ENV GROUPNAME=$USER
ENV UID=1001
ENV GID=1002

RUN apk add --no-cache --update-cache hdf5-dev netcdf-dev libc-dev

# Install basic web server tools and create non-root user
RUN apk update && apk add \
    vim gcc && \
    rm -rf /var/lib/apt/lists/* && \
    addgroup --gid "$GID" "$GROUPNAME" && \
    adduser --disabled-password --ingroup "$GROUPNAME" --uid "$UID" $USER

USER $USER
WORKDIR /home/$USER

COPY ./builds/gdsc/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt