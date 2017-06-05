echo 'deb http://mirrors.aliyun.com/raspbian/raspbian/ wheezy main non-free contrib\ndeb-src http://mirrors.aliyun.com/raspbian/raspbian/ wheezy main non-free contrib' | sudo tee /etc/apt/sources.list.d/hypriot.list

sudo apt-get install -y apt-transport-https 

sudo wget -q https://packagecloud.io/gpg.key -O - | sudo apt-key add - 

sudo echo 'deb https://packagecloud.io/Hypriot/Schatzkiste/debian/ wheezy main' | sudo tee /etc/apt/sources.list.d/hypriot.list

sudo apt-get update 

sudo apt-get install -y docker-hypriot

sudo systemctl enable docker

sudo usermod -aG docker pi

./run.sh
