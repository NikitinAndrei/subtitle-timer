import re,csv


def read_timestamps(name: str, folder='Subsnaudios/'):
    """

    :param name: имя файла
    :param folder: имя папки
    :return: возвращает список (дополнительно сохраняет csv)
    """
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
    time_in_secs = []
    for i, n in enumerate(starts):
        time_in_secs.append(starts[i])
        time_in_secs.append(finishes[i])
        time_in_secs.append(1)
    with open(f'{folder}/{name[:-3]}csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(time_in_secs)
    return time_in_secs


def parse_to_sec(timestamp: str):

    """
    :param timestamp: файл в чч:мм:сс
    :return: в секундах
    """

    time = re.match(r'(\d+):(\d+):(\d+),(\d+)', timestamp)
    return int(time.group(1)) * 3600 + int(time.group(2)) * 60 + int(time.group(3)) + int(time.group(4))/1000


read_timestamps('taxi_subs_7.srt')