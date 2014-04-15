#!/bin/sh

cd `dirname $0`
#deploying basic configuration (dns+zone+key) and dnscherry.ini
./tests/cfg/deploy.sh

#starting dnscherryd
dnscherryd -d -p /tmp/dnscherry.pid -c /etc/dnscherry/dnscherry.ini

#sleep a few seconds
sleep 5

#stoping dnscherryd
pkill dnscherryd
