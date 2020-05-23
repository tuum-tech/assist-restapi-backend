#!/bin/bash 

docker container stop assist-mongo || true && docker container rm -f assist-mongo || true

# start a mongodb docker container
docker run -d --name assist-mongo                     \
    -e MONGO_INITDB_ROOT_USERNAME=mongoadmin          \
    -e MONGO_INITDB_ROOT_PASSWORD=assistmongo         \
    -p 27017:27017                                      \
    mongo
