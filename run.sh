sudo docker rm -f magi
sudo docker run -d -it --name="magi" -v $(pwd)/config:/config -v /etc/localtime:/etc/localtime:ro --net=host bridgenew 
sudo docker logs magi 
