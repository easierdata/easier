# Loop through each line in file_list.txt
while read -r filename; do
    # Use rsync to transfer the file
    rsync -avzhP -e "ssh -i ~/easier/data/keychains/umd-easier-aws.cer"\
     ~/easier/easier/data/landsat/piknik/${filename} \
     ec2-user@ec2-44-213-73-219.compute-1.amazonaws.com:/media/hdd/data/landsat9/piknik
done < $1