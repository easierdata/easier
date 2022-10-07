#!/bin/bash
FILES="../../data/input/*"
for f in $FILES
do
  echo "Processing $f"
    gdal_translate $f "${f%.*}".cog -of COG -co COMPRESS=LZW -co TILED=YES
done