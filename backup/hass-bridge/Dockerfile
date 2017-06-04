FROM magihome/homeassistant:latest
MAINTAINER jin.yang <magihome@qq.com>

# Install homebridge
RUN curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash
RUN sudo apt-get update && sudo apt-get install -y nodejs
RUN sudo apt-get update && sudo apt-get -y install libavahi-compat-libdnssd-dev
RUN sudo npm install -g -unsafe-perm homebridge hap-nodejs node-gyp
WORKDIR /usr/lib/node_modules/homebridge/
RUN sudo npm install -unsafe-perm bignum
WORKDIR /usr/lib/node_modules/hap-nodejs/node_modules/mdns
RUN sudo node-gyp BUILDTYPE=Release rebuild
WORKDIR /
RUN sudo npm install -g homebridge-homeassistant
RUN apt-get install --reinstall avahi-daemon
RUN sed -i 's/rlimit-nproc/#rlimit-nproc/' /etc/avahi/avahi-daemon.conf
RUN sed -i 's/AVAHI_DAEMON_DETECT_LOCAL=1/AVAHI_DAEMON_DETECT_LOCAL=0/' /etc/default/avahi-daemon

# Copy config.json
WORKDIR /root
RUN sudo mkdir .homebridge
COPY config.json /root/.homebridge/config.json

WORKDIR /usr/src/app
COPY run.sh /usr/src/app/run.sh

CMD [ "./run.sh" ]
