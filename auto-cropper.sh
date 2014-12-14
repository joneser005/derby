#!/bin/sh
#pic-crop-save.sh

infile=$1
outfile=`echo $1 | sed 's/.*\/\(.*\)/\1/'`

echo infile=$infile
echo outfile=$outfile
sleep 2
convert $infile -fuzz 30% -gravity Center -trim -resize 220x310 ~/python/derby/from-camera/cropped/$outfile
