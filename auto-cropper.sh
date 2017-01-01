#!/bin/sh
#pic-crop-save.sh

PIC_PATH=derbysite/media/racers

mogrify -fuzz 30% -gravity Center -trim -resize 220x310 ${PIC_PATH}/*
