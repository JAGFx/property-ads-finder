FROM php:8-apache

WORKDIR /srv
ADD . /srv
COPY src/. /var/www/html

RUN apt update -y \
    && apt upgrade -y \
    && apt install cron -y \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt install nodejs -y \
    && npm i \
    && apt install python3 -y \
    && apt install python3-pip -y \
    && pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && crontab /srv/cron/update  \

CMD ["cron"]
