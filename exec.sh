#!/bin/bash
if [ -z $1 ];
then
    docker exec -it hass /bin/bash
else
    docker exec -it -u $1 hass /bin/bash
fi
