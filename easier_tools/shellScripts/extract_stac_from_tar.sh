#usage: extract_stac_from_tar.sh datestr(20220501)

stac_path="./data/stac/landsat-c2l1/json"
datestr=$1
find ./data/landsat/m2m_download/$datestr -name "*stac.json" | while read fname; do

  f="$(basename -- $fname)"
  dest="$stac_path/$datestr"
  echo $dest
  mkdir -p $dest && rsync -avzhP --update $fname $dest
  #tar -xvf $fname -C ../stac/landsat-c2l1/json/ --strip-components 1 --wildcards --no-anchored '*stac.json'
done
