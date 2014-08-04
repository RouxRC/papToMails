#!/bin/bash

cd $(echo $0 | sed 's#/[^/]*$##')/..

if test -f lock.pid; then
  exit 1
fi
echo $$ > lock.pid

source /usr/local/bin/virtualenvwrapper.sh
workon papToMails
python papToMails.py
deactivate

rm -f lock.pid
