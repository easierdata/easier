# chirps
#tifs/netcdf/bils/cogs
output_dir=""

# wget -m -e robots=off -nH --cut-dirs=2 --reject-regex '\?' -R .html,.tmp,.DS_Store -np -r https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs/ -P $output_dir
# wget -m -e robots=off -nH --cut-dirs=2 --reject-regex '\?' -R .html,.tmp,.DS_Store -np -r https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/ -P $output_dir
# wget -m -e robots=off -nH --cut-dirs=2 --reject-regex '\?' -R .html,.tmp,.DS_Store -np -r https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/bils/ -P $output_dir
# wget -m -e robots=off -nH --cut-dirs=2 --reject-regex '\?' -R .html,.tmp,.DS_Store -np -r https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/cogs/ -P $output_dir
wget -m -e robots=off -nH --cut-dirs=2 --reject-regex '\?' -R .html,.tmp,.DS_Store -np -r https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/ -P $output_dir
