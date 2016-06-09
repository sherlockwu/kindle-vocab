#!/usr/bin/env bash
CONTAINER=$1
RUNNING=$(docker inspect --format="{{ .State.Running }}" $CONTAINER 2> /dev/null)
notexist=$?

if [ $notexist -eq 0 ]; then
    if [ $RUNNING == "false" ]; then

	# exists, but not running.  Just rm it
	docker rm $CONTAINER
	notexist=1
    fi
fi

if [ $notexist -eq 1 ]; then
    docker run --name=$CONTAINER -d -p 0:80 -v `pwd`/static:/usr/share/nginx/html:ro nginx
fi

PORT=$(docker inspect --format='{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}' $CONTAINER)
echo "The static content is running locally on $PORT"
