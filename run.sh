sudo docker stop hass
sudo docker rm hass
sudo docker stop bridge
sudo docker rm bridge
sudo docker run -d -it --name="hass" -v $(pwd)/config:/config -v /etc/localtime:/etc/localtime:ro --net=host magihome/homeassistant:latest
sudo docker run -d -it --name="bridge" -v $(pwd)/config/homebridge:/root/.homebridge --net=host magihome/homebridge:latest
