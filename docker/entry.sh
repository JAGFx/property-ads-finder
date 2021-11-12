#!/bin/bash

service cron start
./docker/updater.sh
exec "$@"