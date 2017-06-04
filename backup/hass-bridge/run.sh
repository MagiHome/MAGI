#/bin/sh
sudo /etc/init.d/dbus restart && sudo service avahi-daemon restart
homebridge &
python -m homeassistant --config /config
