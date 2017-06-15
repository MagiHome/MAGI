sudo docker stop hass
sudo docker rm hass
sudo docker stop bridge
sudo docker rm bridge
sudo docker stop airplay
sudo docker rm airplay
sudo docker run -d -it --privileged --name="hass" -v $(pwd)/config:/config -v /dev/snd:/dev/snd -v /etc/localtime:/etc/localtime:ro --net=host magihome/homeassistant:latest 
sudo docker run -d -it --name="bridge" -v $(pwd)/config/homebridge:/root/.homebridge --net=host magihome/homebridge:latest
sudo docker run -d -it --privileged --name="airplay" --device=/dev/snd:/dev/snd -v $(pwd)/config/airplay/shairport-sync.conf:/usr/local/etc/shairport-sync.conf --net=host magihome/airplay:latest
