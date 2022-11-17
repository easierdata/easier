##########################################
# Download large number of scenes by batch
# Usage: sh downloader_m2m.sh batch_folder
##########################################
source ../../venv/bin/activate
cd ../pyScripts
count=1
batch=$1
for i in `find ../../data/landsat/task/$batch -type f -name "scenes_*.txt"`; do
    echo "starting $i"
    python landsat_from_m2m.py -f bundle -s $i > /dev/null && rm $i
    #
    echo "finished $count"
    count=`expr $count + 1`
done