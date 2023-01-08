import csv, re, srt


def read_timestamps(name: str, folder='Subsnaudios/'):
    if not name.endswith('.srt') and '.' not in name:
        name += '.srt'
    with open(f'{folder}/{name}', 'r') as f:
        lines = ''.join(f.readlines())
    start = re.compile(r'\n?[0-9]+:[0-9]{2}:[0-9]{2},[0-9]+')
    sub_start = re.findall(start, lines)
    starts = [i[1:] for i in sub_start if i.startswith('\n')]
    finishes = [i for i in sub_start if not i.startswith('\n')]
    starts = [parse_to_sec(i) for i in starts]
    finishes = [parse_to_sec(i) for i in finishes]


def parse_to_sec(timestamp: str):
    time = re.match(r'(\d+):(\d+):(\d+),(\d+)', timestamp)
    return int(time.group(1)) * 3600 + int(time.group(2)) * 60 + int(time.group(3)) + int(time.group(4))/1000


read_timestamps('taxi_subs_4.srt')

# def make_seconds