FROM php:8-apache

LABEL org.opencontainers.image.source https://github.com/JAGFx/property-ads-finder
ENV TZ=Europe/Paris
ENV APACHE_DOCUMENT_ROOT /srv/src

WORKDIR /srv
ADD . /srv
COPY docker/php.ini $PHP_INI_DIR/conf.d/10-local.ini
RUN mv "$PHP_INI_DIR/php.ini-development" "$PHP_INI_DIR/php.ini"

RUN apt update -y \
    && apt upgrade -y \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt install nodejs -y \
    && apt install python3 -y \
    && apt install python3-pip -y \
    && pip3 install --upgrade pip pyopenssl \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt install cron -y \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && npm i \
    && sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf \
    && sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf \
    && crontab /srv/cron/update

ENTRYPOINT  ["bash", "docker/entry.sh"]
CMD ["docker-php-entrypoint", "apache2-foreground"]