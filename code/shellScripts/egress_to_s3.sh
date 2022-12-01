startdate="20211107"
enddate="20220501"
datestr="$startdate"
bucket="piknik:uofm-data1"
module load rclone
while [ "$(date -d "$datestr" +%Y%m%d)" -lt "$(date -d "$enddate" +%Y%m%d)" ]; do
    echo $datestr
    rclone sync --checkers 50 --retries 6 --s3-upload-concurrency 32 --transfers 16 --s3-chunk-size 100M data/landsat/m2m_download/$datestr $bucket/landsat9-c2-l1/$datestr
    datestr=$(date +%Y%m%d -d "$datestr + 1 day" )
done