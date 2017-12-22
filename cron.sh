#!/bin/sh
set -eux

d=$(dirname $0)
cd $d
date

/usr/local/bin/python3 wunderlog.py norway/asker Norway/Akershus/Asker/Asker

