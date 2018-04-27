day_mepoch=$(($(date --date="1 day ago" +%s%N)/1000000))
day_stamp=$(date --date="1 day ago" +%d%m%y)

echo $day_mepoch
echo $day_stamp


if  [[ ! -d test_data/$day_stamp ]]; then
  mkdir test_data/$day_stamp
  scripts/create_test_data.py $day_mepoch $day_stamp
fi

for interval in 15m 5m 3m 1m; do

./test_backend.py -s -i $interval -d $day_stamp 2>&1 | tee log/serial-${day_stamp}-${interval}.log

done
