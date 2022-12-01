startdate="20211106"
enddate="20211201"
datestr="$startdate"
module load rclone
while [ "$(date -d "$datestr" +%Y%m%d)" -lt "$(date -d "$enddate" +%Y%m%d)" ]; do
    echo $datestr
    rclone sync --checkers 50 --retries 6 --s3-upload-concurrency 32 --transfers 16 --s3-chunk-size 100M data/landsat/m2m_download/$datestr piknik:uofm-data1/landsat9-c2-l1/$datestr
    datestr=$(date +%Y%m%d -d "$d + 1 day" )
done