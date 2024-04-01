module load gdal
gdalwarp -tr 300 300 \
../../data/landsat/m2m_download/LC09_L1TP_031016_20220625_20230409_02_T1_B4.TIF \
../../data/output/downscaled_test_L9_B4.TIF