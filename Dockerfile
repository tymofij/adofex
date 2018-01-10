FROM ubuntu:17.10
RUN apt-get update
RUN apt-get install -y git python-dev python-pip python-pillow gettext redis-server locales

RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN echo "LANG=en_US.UTF-8" > /etc/locale.conf
RUN locale-gen en_US.UTF-8
