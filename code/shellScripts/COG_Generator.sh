#!/bin/bash
module load gdal/3.1.0 #for cluster usage
FILES="./data/input/*.TIF"
for f in $FILES
do
  echo "Processing $f"
  gdal_translate $f "${f%.*}".cog -of COG -co COMPRESS=LZW
  #new finding: After GDAL/3.1.0, there is no TILED parameter and it is automatically included
  #source: https://gdal.org/drivers/raster/cog.html
done