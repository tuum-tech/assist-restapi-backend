#!/usr/bin/env bash
echo "Install required packages"

case `uname` in
    Linux )
        sudo apt-get update -y 
        sudo apt-get install build-essential python3 python3-dev libleveldb-dev -y
        ;;
    Darwin )
        brew update
        brew install leveldb python3
        ;;
    *)
    exit 1
    ;;
esac

type virtualenv >/dev/null 2>&1 || { echo >&2 "No suitable python virtual env tool found, aborting"; exit 1; }

rm -rf .venv
virtualenv -p `which python3` .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt