FROM alpine

# Initialize
RUN mkdir -p /data/web
WORKDIR /data/web
COPY ./docker/web/requirements.txt /data/web/
COPY manage.py /data/web

# Setup
RUN apk update
RUN apk upgrade
RUN apk add --update python3 python3-dev postgresql-client postgresql-dev build-base gettext zlib-dev jpeg-dev libffi-dev
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Clean
RUN apk del -r python3-dev postgresql

# Prepare
COPY ./school/ /data/web/school/
RUN mkdir -p /data/web/site_media
RUN mkdir -p /data/web/media
RUN mkdir -p /data/web/smedia
