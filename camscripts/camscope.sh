#!/bin/sh
cd $1
./mjpg_streamer -i "./input_uvc.so -d /dev/video0" -o "./output_http.so -p $2 -w /www"
