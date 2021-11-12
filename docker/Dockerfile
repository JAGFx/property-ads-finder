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
    && apt install -y \
    cron \
    nodejs \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir --upgrade pip pyopenssl \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt purge --auto-remove \
    && apt clean

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && npm i \
    && crontab /srv/cron/update \
    && sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf \
	&& sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf \
	&& chmod u+x -R docker

ENTRYPOINT  ["bash", "docker/entry.sh"]
CMD ["docker-php-entrypoint", "apache2-foreground"]