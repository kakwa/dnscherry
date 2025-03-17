#!/bin/sh

sudo DEBIAN_FRONTEND=noninteractive apt-get install bind9 -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -f -q -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install slapd -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -f -q -y
sudo rsync -a `dirname $0`/ /
sudo chown -R bind:bind /etc/bind/
sudo systemctl restart bind9 || sudo service bind9 restart || sudo /etc/init.d/bind9 restart
cd `dirname $0`/../../
sudo sed -i "s%template_dir.*%template_dir = '`pwd`/resources/templates/'%" /etc/dnscherry/dnscherry.ini
sudo sed -i "s%tools.staticdir.dir.*%tools.staticdir.dir = '`pwd`/resources/static/'%" /etc/dnscherry/dnscherry.ini

sudo chown -R openldap:openldap /etc/ldap/ || true
rm -f '/etc/ldap/slapd.d/cn=config/olcDatabase={1}mdb.ldif' || true
rm -f '/etc/ldap/slapd.d/cn=config/olcBackend={0}mdb.ldif' || true
sudo systemctl restart slapd || sudo service slapd restart || sudo /etc/init.d/slapd restart
ldapadd -H ldap://localhost -x -D "cn=admin,dc=example,dc=org" -f /etc/ldap/content.ldif -w password || true
sed -i "s/\(127.0.0.1.*\)/\1 ldap.dnscherry.org/" /etc/hosts || true
