FROM ghcr.io/osgeo/gdal:ubuntu-full-latest

ENV USER=gdsc
ENV GROUPNAME=$USER
ENV UID=1001

# Install basic web server tools and create non-root user
RUN apt-get update && apt-get install -y \
    vim p7zip-full && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u "$UID" $USER

RUN mkdir -p -m 444 /openssl
COPY --chmod=444 ./builds/osgeo/openssl.conf /openssl/openssl.conf

USER $USER