#!/bin/bash 

docker container stop assist-postgres || true && docker container rm -f assist-postgres || true

# start a postgres docker container
docker run -d --name assist-postgres \
    -v "$PWD/.postgres-data:/var/lib/postgresql/data"     \
    -e POSTGRES_DB=assistdb                             \
    -e POSTGRES_USER=ast                                \
    -e POSTGRES_PASSWORD=ast                            \
    -p 5438:5432                                        \
    postgres:11-alpine
