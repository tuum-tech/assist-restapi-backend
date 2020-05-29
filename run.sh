#!/usr/bin/env bash

function start () {
    docker container stop assist-mongo || true && docker container rm -f assist-mongo || true
    docker run -d --name assist-mongo                     \
        -e MONGO_INITDB_ROOT_USERNAME=mongoadmin          \
        -e MONGO_INITDB_ROOT_PASSWORD=assistmongo         \
        -p 27017:27017                                      \
        mongo

    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    gunicorn -b 0.0.0.0:8000 --reload app.main:application
}

function stop () {
    docker container stop assist-mongo || true && docker container rm -f assist-mongo || true
    ps -ef | grep gunicorn | awk '{print $2}' | xargs kill -9
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    *)
    echo "Usage: run.sh {start|stop}"
    exit 1
esac