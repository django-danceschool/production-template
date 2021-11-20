FROM python:3.10-slim-bullseye

# Initialize
RUN mkdir -p /data/web
WORKDIR /data/web
COPY ./requirements.txt /data/web/
COPY ./custom/requirements.txt /data/web/requirements_custom.txt
COPY manage.py /data/web

# Setup
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install postgresql-client gettext gcc gettext zlib1g libjpeg-dev python3-cffi libffi-dev git musl-dev libpango-1.0-0 libpangocairo-1.0-0 python3-cairo-dev libjxr-tools libgdk-pixbuf2.0-dev shared-mime-info fonts-liberation2
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements_custom.txt

# Add custom apps to PYTHONPATH
ENV PYTHONPATH "$PYTHONPATH:/data/web/custom"

# Clean
RUN apt-get -y remove postgresql-client git
RUN apt -y autoremove

# Prepare
COPY ./school/ /data/web/school/
