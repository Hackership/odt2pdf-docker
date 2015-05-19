FROM ubuntu:trusty
MAINTAINER Benjamin Kampmann <ben@hackership.org>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install -q -y python python-pip python-virtualenv python-uno \
    gunicorn supervisor \
    libreoffice libreoffice-writer ure libreoffice-java-common libreoffice-core \
    libreoffice-common openjdk-7-jre \
    fonts-opensymbol hyphen-fr hyphen-de hyphen-en-us hyphen-it hyphen-ru \
    fonts-dejavu fonts-dejavu-core fonts-dejavu-extra fonts-droid fonts-dustin \
    fonts-f500 fonts-fanwood fonts-freefont-ttf fonts-liberation fonts-lmodern \
    fonts-lyx fonts-sil-gentium fonts-texgyre fonts-tlwg-purisa && \
    apt-get -q -y remove libreoffice-gnome

RUN rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app

ADD requirements.txt /app/requirements.txt
ADD app.py /app/app.py

RUN pip install -r /app/requirements.txt

ADD supervisor.flask.conf /etc/supervisor/conf.d/flask.conf
ADD supervisor.libreoffice.conf /etc/supervisor/conf.d/libreoffice.conf

# EXPOSE 8997
EXPOSE 5000

CMD supervisord -n