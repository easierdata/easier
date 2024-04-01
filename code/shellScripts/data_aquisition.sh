# token= .env
year="2015"
output_dir=""
dataset="MOD09Q1G_NDVI"
#dataset="MOD09"
#echo "dry run $token"
for i in {1..361..8}
#for i in {1..366}
do
    target=$(printf %03d $i)
    echo "$target"
    wget -e robots=off -m -np -R .html,.tmp -nH --cut-dirs=3 "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/6/$dataset/$year/$target/" --header "Authorization: Bearer $token" -P "$output_dir"
done
