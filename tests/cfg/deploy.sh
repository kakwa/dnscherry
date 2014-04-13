#!/bin/sh

sudo rsync -a `dirname $0`/ /
sudo chown -R bind:bind /etc/bind/
sudo /etc/init.d/bind9 restart
