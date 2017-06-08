export LD_LIBRARY_PATH=$(pwd)/../libs/RaspberryPi/
make clean;make
cp ../bin/tts ../ttsbin/
cp ../libs/RaspberryPi/libmsc.so ../ttsbin
