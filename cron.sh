#!/bin/sh
test -f ~/.netrc && chmod 0600 ~/.netrc
set -eu
d=$(dirname $0)
cd $d
date
set -x
/usr/local/bin/python3 wunderlog.py norway/asker Norway/Akershus/Asker/Asker

