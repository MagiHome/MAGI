FROM resin/armv7hf-debian
MAINTAINER jin.yang <magihome@qq.com>

# Install homebridge
RUN sudo apt-get update
RUN sudo apt-get install avahi-daemon libavahi-client-dev libssl-dev libpolarssl-dev libsoxr-dev
RUN sudo apt-get install libasound2-dev
RUN sudo apt-get install libconfig-dev 
RUN sudo apt-get install libpopt-dev
RUN sudo apt-get install build-essential git autoconf automake libtool
RUN sudo apt-get install libdaemon-dev
COPY shairport-sync shairport-sync
WORKDIR shairport-sync
RUN autoreconf -i -f
RUN sudo ./configure --with-alsa --with-avahi --with-ssl=openssl --with-metadata --with-soxr --with-systemd --with-systemdsystemunitdir=/lib/systemd/system
RUN make
RUN getent group shairport-sync &>/dev/null || sudo groupadd -r shairport-sync >/dev/null
RUN getent passwd shairport-sync &> /dev/null || sudo useradd -r -M -g shairport-sync -s /usr/bin/nologin -G audio shairport-sync >/dev/null
RUN sudo make install

COPY run.sh run.sh

CMD [ "./run.sh" ]
