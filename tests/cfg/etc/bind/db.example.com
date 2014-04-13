$ORIGIN .
$TTL 3600	; 1 hour
example.com		IN SOA	ns.example.com. username.example.com. (
				2007120799 ; serial
				86400      ; refresh (1 day)
				7200       ; retry (2 hours)
				2419200    ; expire (4 weeks)
				3600       ; minimum (1 hour)
				)
			NS	ns.example.com.
			NS	ns.somewhere.example.
$ORIGIN example.com.
123			A	192.168.0.4
asda			A	192.168.0.16
asdaaaa			A	192.168.0.11
asdaasd			CNAME	asd
asds			A	192.168.0.20
ns			AAAA	2001:db8:10::2
www			A	192.168.0.4
