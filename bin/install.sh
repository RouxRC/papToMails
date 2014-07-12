#!/bin/bash

sudo apt-get install virtualenvwrapper

source $(which virtualenvwrapper.sh)
mkvirtualenv --no-site-packages papToMails
workon papToMails
pip install -r requirements.txt
add2virtualenv .
deactivate

if ! test -e config.py; then
  cp config.py{.example,}
  echo "Please edit config.py to configure pap url & emails"
fi
