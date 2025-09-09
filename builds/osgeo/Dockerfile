FROM osgeo/gdal:ubuntu-full-3.6.3

# Install basic web server tools and create non-root user
RUN apt-get update && apt-get install -y \
    vim p7zip-full && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /openssl
COPY ./builds/osgeo/openssl.conf /openssl/openssl.conf