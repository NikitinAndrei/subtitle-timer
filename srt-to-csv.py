import csv, re, srt

with open('Subsnaudios/taxi_subs_12.srt', 'r') as f:
    subs = srt.parse(f)
    for line in f:
        print(f)
