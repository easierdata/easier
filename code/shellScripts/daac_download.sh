#setting up following
## https://git.earthdata.nasa.gov/projects/LPDUR/repos/daac_data_download_python/browse
datestr=$1
mkdir -p ./data/$datestr
rm files.txt
daac_directory="https://e4ftl01.cr.usgs.gov/GEDI/GEDI01_B.002/$datestr/"
(curl $daac_directory | grep -oP '<a href=".+?">\K.+?(?=<)' ) >> files.txt
while IPS= read -r file; do
    if [[ $file = GEDI* ]];
    then
        echo "python DAACDataDownload.py -dir ./data/$datestr -f $daac_directory$file"
        python DAACDataDownload.py -dir ./data/$datestr -f $daac_directory$file
    else
        echo "invalid $file";
    fi;
done < files.txt;

#python DAACDataDownload.py -dir ./data -f https://e4ftl01.cr.usgs.gov/GEDI/GEDI01_B.002/2022.10.25/GEDI01_B_2022298002227_O21900_02_T05580_02_005_02_V002.h5
