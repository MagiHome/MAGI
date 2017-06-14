#!/bin/bash
service avahi-daemon stop
rm -rf /var/run/avahi-daemon/
rm -rf /var/run/dbus
mkdir /var/run/dbus
mkdir /var/run/avahi-daemon/pid
id avahi
x=$((9000 + RANDOM % 1000))
usermod -u $x avahi
dbus-daemon --system
sleep 1
service avahi-daemon start
sleep 2
/usr/local/bin/shairport-sync
