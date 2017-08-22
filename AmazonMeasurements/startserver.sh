#!/bin/sh

echo "Starting server 12300"
cd "/server"
nohup java -jar server.jar 12300 12300 >/dev/null 2>&1 &
