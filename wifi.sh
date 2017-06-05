sudo ifconfig wlan0 down
sudo ifconfig wlan0 up
sudo wpa_supplicant -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
sudo dhcpcd wlan0
