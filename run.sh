#!/usr/bin/env bash

function start () {
    docker container stop tuum-mongo || true && docker container rm -f tuum-mongo || true
    docker run -d --name tuum-mongo                     \
        -v ${HOME}/.tuum-mongodb-data:/data/db                \
        -e MONGO_INITDB_ROOT_USERNAME=mongoadmin        \
        -e MONGO_INITDB_ROOT_PASSWORD=mongopass         \
        -p 27017:27017                                  \
        mongo

    virtualenv -p `which python3.7` .venv
    source .venv/bin/activate
    pip install --upgrade pip

    case `uname` in
    Linux )
        pip install -r requirements.txt
        ;;
    Darwin )
        pip install --global-option=build_ext \
                    --global-option="-I/usr/local/include" --global-option="-L/usr/local/lib" \
                    --global-option="-I/usr/local/opt/zlib/include" --global-option="-L/usr/local/opt/zlib/lib" -r requirements.txt
        ;;
    *)
    exit 1
    ;;
    esac

    gunicorn -b 0.0.0.0:8000 --reload app:application
}

function stop () {
    docker container stop tuum-mongo || true && docker container rm -f tuum-mongo || true
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