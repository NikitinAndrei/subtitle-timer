import csv, re, srt

with open('taxi_subs_4.srt', 'r') as f:
    subs = srt.parse(f)
    for line in f:
        print(f)
