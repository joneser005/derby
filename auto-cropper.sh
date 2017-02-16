#!/bin/sh
#pic-crop-save.sh

PIC_PATH=derbysite/media/racers

mogrify -gravity Center -resize 220x310 ${PIC_PATH}/*
