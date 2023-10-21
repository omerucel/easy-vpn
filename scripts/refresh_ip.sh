#!/bin/bash
#
# Original: https://github.com/Nyr/openvpn-install
# The original script simplified for Ubuntu.
#
cp /home/ubuntu/scripts/files/server.conf /etc/openvpn/server/server.conf
cp /home/ubuntu/scripts/files/99-openvpn-forward.conf /etc/sysctl.d/99-openvpn-forward.conf
cp /home/ubuntu/scripts/files/ip_forward.txt /proc/sys/net/ipv4/ip_forward
cp /home/ubuntu/scripts/files/openvpn-iptables.service /etc/systemd/system/openvpn-iptables.service
cp /home/ubuntu/scripts/files/client-common.txt /etc/openvpn/server/client-common.txt
sed -e "s/IP_ADDRESS/$1/g" -i /etc/openvpn/server/client-common.txt
sed -e "s/PRIVATE_IP_ADDRESS/$2/g" -i /etc/systemd/system/openvpn-iptables.service
sed -e "s/IP_ADDRESS/$1/g" -i /etc/openvpn/server/server.conf
sed -e "s/PRIVATE_IP_ADDRESS/$2/g" -i /etc/openvpn/server/server.conf
systemctl enable --now openvpn-iptables.service
systemctl enable --now openvpn-server@server.service
systemctl restart openvpn-iptables.service
systemctl restart openvpn-server@server.service

{
cat /etc/openvpn/server/client-common.txt
echo "<ca>"
cat /etc/openvpn/server/easy-rsa/pki/ca.crt
echo "</ca>"
echo "<cert>"
sed -ne '/BEGIN CERTIFICATE/,$ p' /etc/openvpn/server/easy-rsa/pki/issued/client.crt
echo "</cert>"
echo "<key>"
cat /etc/openvpn/server/easy-rsa/pki/private/client.key
echo "</key>"
echo "<tls-crypt>"
sed -ne '/BEGIN OpenVPN Static key/,$ p' /etc/openvpn/server/tc.key
echo "</tls-crypt>"
} > /home/ubuntu/client.ovpn
chown ubuntu:ubuntu /home/ubuntu/client.ovpn