startdate="20211107"
enddate="20220501"
datestr="$startdate"
bucket="piknik:uofm-data1"
module load rclone
while [ "$(date -d "$datestr" +%Y%m%d)" -lt "$(date -d "$enddate" +%Y%m%d)" ]; do
    echo $datestr
    # Uncomment to extract stac information from the bundle
    #sh code/shellScripts/extract_stac_from_tar.sh $datestr
    
    #Option 1: move files to save space
    
    #rclone move -v --delete-empty-src-dirs --ignore-existing --checkers 50 --retries 6 --s3-upload-concurrency 32 --transfers 16 --s3-chunk-size 100M data/landsat/m2m_download/$datestr piknik:uofm-data1/landsat9-c2-l1/$datestr
    
    #Option 2: force update for bug files
    #rclone copy -v --ignore-existing --checkers 50 --retries 6 --s3-upload-concurrency 32 --transfers 16 --s3-chunk-size 100M data/landsat/m2m_download/$datestr piknik:uofm-data1/landsat9-c2-l1/$datestr
    #rclone copy -v --ignore-existing --checkers 50 --retries 6 --s3-upload-concurrency 32 --transfers 16 --s3-chunk-size 100M data/landsat/landsat9-c2-l1-missing piknik:uofm-data1/landsat9-c2-l1-missing
    
datestr=$(date +%Y%m%d -d "$datestr + 1 day" )
done