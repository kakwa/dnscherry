$ORIGIN example2.com.     ; designates the start of this zone file in the namespace
$TTL 1h                  ; default expiration time of all resource records without their own TTL value
example2.com.  IN  SOA  ns.example2.com. username.example2.com. (
              2007120710 ; serial number of this zone file
              1d         ; slave refresh (1 day)
              2h         ; slave retry time in case of a problem (2 hours)
              4w         ; slave expiration time (4 weeks)
              1h         ; maximum caching time in case of failed lookups (1 hour)
              )
example2.com. NS    ns                    ; ns.example2.com is a nameserver for example2.com
example2.com. MX    10 mail.example2.com.  ; mail.example2.com is the mailserver for example2.com
@             MX    20 mail2.example2.com. ; equivalent to above line, "@" represents zone origin
@             MX    50 mail3              ; equivalent to above line, but using a relative host name
example2.com. A     192.0.2.1             ; IPv4 address for example2.com
ns            A     192.0.2.2             ; IPv4 address for ns.example2.com
truc          CNAME example2.com.          ; www.example2.com is an alias for example2.com
machine       CNAME www                   ; wwwtest.example2.com is another alias for www.example2.com
mail3         A     192.0.2.5             ; IPv4 address for mail3.example2.com
