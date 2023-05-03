start='2019-04-19'
end='2022-10-23'

start=$(date -d $start +%Y-%m-%d)
end=$(date -d $end +%Y-%m-%d)
while [ $start != $end ]
do
    echo 
    startdate=$(date -d $start +%Y.%m.%d)
    #do something
    sh ../easier/code/shellScripts/daac_download.sh $startdate

    start=$(date -d"$start + 1 day" +"%Y-%m-%d")

done