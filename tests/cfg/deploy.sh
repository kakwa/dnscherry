#!/bin/sh

sudo DEBIAN_FRONTEND=noninteractive apt-get install bind9 -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -f -q -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install slapd -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -f -q -y

[ -e '/etc/default/slapd' ] && rm -rf /etc/default/slapd
cp -r `dirname $0`/etc/default/slapd /etc/default/slapd
[ -e '/etc/ldap' ] && rm -rf /etc/ldap
cp -r `dirname $0`/etc/ldap /etc/ldap
sudo chown -R openldap:openldap /etc/ldap/ || true
sudo systemctl restart slapd || sudo service slapd restart || sudo /etc/init.d/slapd restart

ldapadd -c -H ldap://localhost -x -D "cn=admin,dc=example,dc=org" -f /etc/ldap/content.ldif -w password || true
if grep -q '127.0.0.1' /etc/hosts && ! grep -q 'ldap.dnscherry.org' /etc/hosts
then
    sed -i "s/\(127.0.0.1.*\)/\1 ldap.dnscherry.org/" /etc/hosts
else
    echo '127.0.0.1 ldap.dnscherry.org' >> /etc/hosts
fi
cat /etc/hosts

[ -e '/etc/bind' ] && rm -rf /etc/bind
cp -r `dirname $0`/etc/bind /etc/bind
sudo chown -R bind:bind /etc/bind/
sudo systemctl restart bind9 || sudo service bind9 restart || sudo /etc/init.d/bind9 restart

[ -e '/etc/dnscherry' ] && rm -rf /etc/dnscherry
cp -r `dirname $0`/etc/dnscherry /etc/dnscherry
cd `dirname $0`/../../
sudo sed -i "s%template_dir.*%template_dir = '`pwd`/resources/templates/'%" /etc/dnscherry/dnscherry.ini
sudo sed -i "s%tools.staticdir.dir.*%tools.staticdir.dir = '`pwd`/resources/static/'%" /etc/dnscherry/dnscherry.ini


