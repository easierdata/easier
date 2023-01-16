startdate="20211101"
enddate="20221101"
datestr="$startdate"
module load rclone
while [ "$(date -d $datestr +%Y%m%d)" -lt "$(date -d $enddate +%Y%m%d)" ]; do
    echo $datestr
    #sh code/shellScripts/extract_stac_from_tar.sh $datestr
    # move files to save space
    #rclone move -v --delete-empty-src-dirs --ignore-existing --checkers 50 --retries 6 --s3-upload-concurrency 32 --transfers 16 --s3-chunk-size 100M data/landsat/m2m_download/$datestr piknik:uofm-data1/landsat9-c2-l1/$datestr
    #force update for bug files
    #rclone copy -v --ignore-existing --checkers 50 --retries 6 --s3-upload-concurrency 32 --transfers 16 --s3-chunk-size 100M data/landsat/m2m_download/$datestr piknik:uofm-data1/landsat9-c2-l1/$datestr
    
    datestr=$(date +%Y%m%d -d "$datestr + 1 day" )
done
