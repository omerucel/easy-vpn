#!/bin/bash
#
# Original: https://github.com/Nyr/openvpn-install
# The original script simplified for Ubuntu.
#
apt-get update
apt-get install -y --no-install-recommends wget openvpn openssl ca-certificates iptables
mkdir -p /etc/openvpn/server/easy-rsa/
wget https://github.com/OpenVPN/easy-rsa/releases/download/v3.1.7/EasyRSA-3.1.7.tgz
tar xzvf EasyRSA-3.1.7.tgz -C /etc/openvpn/server/easy-rsa/ --strip-components 1
chown -R root:root /etc/openvpn/server/easy-rsa/
cd /etc/openvpn/server/easy-rsa/
./easyrsa --batch init-pki
./easyrsa --batch build-ca nopass
./easyrsa --batch --days=3650 build-server-full server nopass
./easyrsa --batch --days=3650 build-client-full client nopass
./easyrsa --batch --days=3650 gen-crl
cp pki/ca.crt pki/private/ca.key pki/issued/server.crt pki/private/server.key pki/crl.pem /etc/openvpn/server
chown nobody:nogroup /etc/openvpn/server/crl.pem
chmod o+x /etc/openvpn/server/
openvpn --genkey --secret /etc/openvpn/server/tc.key
echo '-----BEGIN DH PARAMETERS-----
MIIBCAKCAQEA//////////+t+FRYortKmq/cViAnPTzx2LnFg84tNpWp4TZBFGQz
+8yTnc4kmz75fS/jY2MMddj2gbICrsRhetPfHtXV/WVhJDP1H18GbtCFY2VVPe0a
87VXE15/V8k1mE8McODmi3fipona8+/och3xWKE2rec1MKzKT0g6eXq8CrGCsyT7
YdEIqUuyyOP7uWrat2DX9GgdT0Kj3jlN9K5W7edjcrsZCwenyO4KbXCeAvzhzffi
7MA0BM0oNC9hkXL+nOmFg/+OTxIy7vKBg8P+OxtMb61zO7X8vC7CIAXFjvGDfRaD
ssbzSibBsu/6iGtCOGEoXJf//////////wIBAg==
-----END DH PARAMETERS-----' > /etc/openvpn/server/dh.pem
