import os
import re
import csv
import pandas as pd
import soundfile as sf
from tqdm import tqdm


def subs_check(path="D:\\Projects\\SubsTimer\\Subsnaudios\\"):
    indexing = {}
    mistakes = {'file name': None, 'time_stamp': None, 'indexing': []}
    for name in os.listdir(path):
        if '.srt' in name:
            with open(f'{path}\{name}', 'r', encoding='utf-8') as f:
                lines = ''.join(f.readlines())
            correct_time = re.compile(r'\n?[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}')
            incorrect_time = re.compile(r'\n?[0-9]+:[0-9]+:[0-9]+,[0-9]+')
            subs_timestamps = re.findall(correct_time, lines)
            subs_misformat = re.findall(incorrect_time, lines)

            if len(subs_misformat) != len(subs_timestamps):
                if not mistakes['file name']:
                    mistakes['file name'] = [name]
                    mistakes['time_stamp'] = []
                else:
                    mistakes['file name'].append(name)
                    mistakes['time_stamp'].append([])
                for i, n in enumerate(subs_misformat):
                    if n != subs_timestamps[n]:
                        mistakes['time_stamp'][-1].append(n)

            starts = [i[1:] for i in correct_time if i.startswith('\n')]
            finishes = [i for i in correct_time if not i.startswith('\n')]
            starts = [parse_to_sec(i) for i in starts]
            finishes = [parse_to_sec(i) for i in finishes]
            time_in_secs = []

            for i, n in enumerate(starts):
                time_in_secs.append(starts[i])
                time_in_secs.append(finishes[i])
                if finishes[i - 1] - starts[i] > 0 and i > 2:
                    raise Exception(f'Mistake in {name} on position {i + 1} with time {parse_to_mins(finishes[i - 1])}')
                time_in_secs.append(1)


def change_indexes(subfile: str, path="D:\\Projects\\SubsTimer\\Subsnaudios\\"):
    with open(path + subfile, 'r', encoding='utf-8') as f:
        data = f.readlines()
    i = 1
    for index, line in enumerate(data):
        if re.match(r'\d+\n', line):
            data[index] = str(i) + '\n'
            i += 1
    with open(path + subfile, 'w', encoding='utf-8') as f:
        f.writelines(data)


def read_timestamps(name: str, folder='/Subsnaudios'):
    """

    :param name: имя файла
    :param folder: имя папки
    :return: возвращает список (дополнительно сохраняет csv)
    """
    path = os.getcwd()
    with open(f'{path + folder}\{name}', 'r', encoding='utf-8') as f:
        lines = ''.join(f.readlines())
    start = re.compile(r'\n?[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]+')
    sub_start = re.findall(start, lines)
    starts = [i[1:] for i in sub_start if i.startswith('\n')]
    finishes = [i for i in sub_start if not i.startswith('\n')]
    starts = [parse_to_sec(i) for i in starts]
    finishes = [parse_to_sec(i) for i in finishes]
    time_in_secs = []

    for i, n in enumerate(starts):

        time_in_secs.append(starts[i])
        time_in_secs.append(finishes[i])
        if finishes[i - 1] - starts[i] > 0 and i > 2:
            raise Exception(f'Mistake in {name} on position {i+1} with time {parse_to_mins(finishes[i - 1])}')
        time_in_secs.append(1)

    return time_in_secs


def parse_to_sec(timestamp: str):
    """
    :param timestamp: файл в чч:мм:сс
    :return: в секундах
    """

    time = re.match(r'(\d+):(\d+):(\d+),(\d+)', timestamp)
    return int(time.group(1)) * 3600 + int(time.group(2)) * 60 + int(time.group(3)) + int(time.group(4)) / 1000


def parse_to_mins(seconds):
    if not float:
        seconds = float(seconds)
    hours = seconds // 3600
    minutes = seconds // 60
    seconds = seconds - 3600 * hours - minutes * 60
    return f'{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}'


def all_srt_to_csv(input_folder='/Subsnaudios'):
    """
    Function makes csv files from srt and creates DB with them
    :param input_folder: folder with subs
    :return:
    """
    path = os.getcwd()
    database = {'name': [], 'time': [], 'duration': []}
    for i in tqdm(os.listdir(path + input_folder)):
        if 'srt' in i:
            file, sr = sf.read(path + input_folder + '/' + i[:-3] + 'mp3')
            time = read_timestamps(i, folder=input_folder)
            database['name'].append(i)
            database['time'].append(time)
            database['duration'].append(len(file) / sr)
            with open(f'{path + input_folder}\{i[:-3]}csv', 'w') as f:
                writer = csv.writer(f)
                writer.writerow(time)
    db = pd.DataFrame(database)
    db.to_csv('Database.csv', index=False)


def database_card(db):
    df = pd.read_csv(db)


all_srt_to_csv()
# change_indexes('taxi_subs_6.srt')


