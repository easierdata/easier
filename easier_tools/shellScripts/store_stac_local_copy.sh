startdate="20220901"
enddate="20221101"
datestr="$startdate"
while [ "$(date -d $datestr +%Y%m%d)" -lt "$(date -d $enddate +%Y%m%d)" ]; do
    echo $datestr
    sh code/shellScripts/extract_stac_from_tar.sh $datestr
    datestr=$(date +%Y%m%d -d "$datestr + 1 day" )
done
