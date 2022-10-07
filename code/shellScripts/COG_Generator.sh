#!/bin/bash
# NOTE : Quote it else use array to avoid problems #
FILES="../../data/input/*"
for f in $FILES
do
  echo "Processing $f"
  # take action on each file. $f store current file name
    gdal_translate $f "${f%.*}".cog -of COG -co COMPRESS=LZW -co TILED=YES
done