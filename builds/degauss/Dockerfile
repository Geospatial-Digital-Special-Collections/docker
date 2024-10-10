# Start from an official Degauss image
FROM ghcr.io/degauss-org/geocoder

# install needed ruby gems
RUN gem install --no-document sinatra \
    && gem install --no-document rackup \
    && gem install --no-document puma

# copy the app and start it running
COPY ./app/ /app
WORKDIR /app
CMD ["ruby","degaussApi.rb -p 4567"]