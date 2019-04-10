FROM alpine

# Initialize
RUN mkdir -p /data/web
WORKDIR /data/web
COPY ./requirements.txt /data/web/
COPY ./custom/requirements.txt /data/web/requirements_custom.txt
COPY manage.py /data/web

# Setup
RUN apk update
RUN apk upgrade
RUN apk add --update python3 python3-dev postgresql-client postgresql-dev build-base gettext zlib-dev jpeg-dev libffi-dev git
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements_custom.txt

# Add custom apps to PYTHONPATH
ENV PYTHONPATH "$PYTHONPATH:/data/web/custom"

# Clean
RUN apk del -r python3-dev postgresql git

# Prepare
COPY ./school/ /data/web/school/
