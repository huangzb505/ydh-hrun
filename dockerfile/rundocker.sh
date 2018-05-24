#!/usr/bin/env bash
git #!/bin/bash
basepath=$(cd `dirname $0`; pwd)
echo $basepath
cd $basepath/..
docker build -t ydhhttprunner_image ./dockerfile/

echo $1
docker run --rm -v $PWD:/app --dns=202.96.134.33 ydhhttprunner_image python ./main.py --env $1

