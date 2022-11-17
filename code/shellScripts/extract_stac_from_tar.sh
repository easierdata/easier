#usage: tar -xvf 086/110/LC09_L1GT_086110_20220306_20220307_02_T2.tar -C ../stac/landsat-c2l1/json/ --strip-components 1 --wildcards --no-anchored '*stac.json'
cd data/landsat
find . -name "*.tar"|while read fname; do
  #echo "$fname"
  tar -xvf $fname -C ../stac/landsat-c2l1/json/ --strip-components 1 --wildcards --no-anchored '*stac.json'
done

