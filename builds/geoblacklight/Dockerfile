FROM ruby

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libxml2-dev libxslt1-dev \
        nodejs \
        npm \
        default-jre \
        default-jdk \
        vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
RUN gem update \
    && gem install rails
RUN git clone https://github.com/geoblacklight/geoblacklight.git .
RUN bundle install
