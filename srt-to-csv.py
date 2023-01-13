import os, re, csv
import pandas as pd


def read_timestamps(name: str, folder='/Subsnaudios'):
    """

    :param name: имя файла
    :param folder: имя папки
    :return: возвращает список (дополнительно сохраняет csv)
    """
    path = os.getcwd()
    with open(f'{path + folder}\{name}', 'r', encoding='utf-8') as f:
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
        if finishes[i - 1] - starts[i] > 0 and i > 2: break
        time_in_secs.append(1)

    return time_in_secs


def parse_to_sec(timestamp: str):
    """
    :param timestamp: файл в чч:мм:сс
    :return: в секундах
    """

    time = re.match(r'(\d+):(\d+):(\d+),(\d+)', timestamp)
    return int(time.group(1)) * 3600 + int(time.group(2)) * 60 + int(time.group(3)) + int(time.group(4)) / 1000


def all_srt_to_csv(input_folder='/Subsnaudios'):
    """
    Function makes csv files from srt and creates DB with them
    :param input_folder: folder with subs
    :return:
    """
    path = os.getcwd()
    database = {'name': [], 'time': []}
    for i in os.listdir(path + input_folder):

        if 'srt' in i:
            time = read_timestamps(i, folder=input_folder)
            database['name'].append(i)
            database['time'].append(time)
            with open(f'{path + input_folder}\{i[:-3]}csv', 'w') as f:
                writer = csv.writer(f)
                writer.writerow(time)
    db = pd.DataFrame(database)
    db.to_csv('Database.csv', index=False)


all_srt_to_csv()
