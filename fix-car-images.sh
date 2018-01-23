#!/bin/sh
PIC_PATH=/home/robb/dev/derby/derbysite/media/racers
mogrify -resize 220x310 -rotate "-90>" -strip ${PIC_PATH}/*
