FROM ubuntu:17.10
RUN apt-get update
RUN apt-get install -y git python-dev python-pip python-pillow gettext redis-server
