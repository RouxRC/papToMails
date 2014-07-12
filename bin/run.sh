#!/bin/bash

cd $(echo $0 | sed 's#/[^/]*$##')

source $(which virtualenvwrapper.sh)
workon papToMails
python papToMails.py
deactivate
