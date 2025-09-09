FROM ghcr.io/osgeo/gdal:ubuntu-full-latest

# Install basic web server tools and create non-root user
RUN apt-get update && apt-get install -y \
    vim p7zip-full && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /openssl
COPY ./builds/osgeo/openssl.conf /openssl/openssl.conf
