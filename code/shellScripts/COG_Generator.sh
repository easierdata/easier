#!/bin/bash
module load gdal #for cluster usage
FILES="../../data/input/*.TIF"
for f in $FILES
do
  echo "Processing $f"
  gdal_translate $f "${f%.*}".cog -of COG -co COMPRESS=LZW
done