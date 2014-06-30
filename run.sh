#!/bin/bash

cd $(echo $0 | sed 's#/[^/]*$##')

source $(which virtualenvwrapper.sh)
workon pap
python papToTweet.py
deactivate
