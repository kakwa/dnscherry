#!/bin/sh

sudo rsync -a `dirname $0`/ /
sudo chown -R bind:bind /etc/bind/
sudo /etc/init.d/bind9 restart
cd `dirname $0`/../../
sudo sed -i "s%template_dir.*%template_dir = '`pwd`/resources/templates/'%" /etc/dnscherry/dnscherry.ini
sudo sed -i "s%tools.staticdir.dir.*%tools.staticdir.dir = '`pwd`/resources/static/'%" /etc/dnscherry/dnscherry.ini

sudo chown -R openldap:openldap /etc/ldap/
sudo /etc/init.d/slapd restart
ldapadd -H ldap://localhost -x -D "cn=admin,dc=example,dc=org" -f /etc/ldap/content.ldif -w password
sed -i "s/\(127.0.0.1.*\)/\1 ldap.dnscherry.org/" /etc/hosts
