import os
import re
import pandas as pd
import soundfile as sf
from tqdm import tqdm


def subs_check(path="D:\\Projects\\SubsTimer\\Subsnaudios\\"):
    mistakes = {'Name': None,
                'time_format': None,
                'indexing': None,
                'starts unfinished': None,
                'good': []
                }
    for name in os.listdir(path):
        if '.srt' in name:
            with open(f'{path}\\{name}', 'r', encoding='utf-8') as f:
                lines = ''.join(f.readlines())
            if not mistakes['Name']:
                mistakes['Name'] = [name]
            else: mistakes['Name'].append(name)

            # Check if it is 00:00:00,000 format
            correct_time = re.compile(r'\n?[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}')
            incorrect_time = re.compile(r'\n?[0-9]+:[0-9]+:[0-9]+,[0-9]+')
            subs_timestamps = re.findall(correct_time, lines)
            subs_misformat = re.findall(incorrect_time, lines)

            if not mistakes['time_format']:
                mistakes['time_format'] = [[]]
            else:
                mistakes['time_format'].append([])

            if len(subs_misformat) != len(subs_timestamps):
                for i, n in enumerate(subs_misformat):
                    if not re.match(r'\n?[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}', n):
                        mistakes['time_format'][-1].append(subs_misformat[i])

            # Checking if a subtitle starts when previous one did not finish
            starts = [i for i in subs_timestamps if i.startswith('\n')]
            finishes = [i for i in subs_timestamps if not i.startswith('\n')]

            starts = [parse_to_sec(i) for i in starts]
            finishes = [parse_to_sec(i) for i in finishes]

            if not mistakes['starts unfinished']:
                mistakes['starts unfinished'] = [[]]
            else:
                mistakes['starts unfinished'].append([])
            for i, n in enumerate(starts):
                if finishes[i - 1] - starts[i] > 0 and i > 2:
                    mistakes['starts unfinished'][-1].append(f'{i + 1}, {finishes[i - 1]}, {starts[i]}')
            # Checking order of indexes for subs
            if not mistakes['indexing']:
                mistakes['indexing'] = [[]]
            else:
                mistakes['indexing'].append([])
            lines = lines.split(sep='\n')

            indexes = []
            for i in lines:
                if re.match(r'\d+$', i):
                    indexes.append(int(i))

            for i, n in enumerate(indexes):
                if n != i + 1:
                    print(i + 1)
                    mistakes['indexing'][-1] = 'Error'
                    break
                else:
                    mistakes['indexing'][-1] = []
            if mistakes['indexing'][-1] or mistakes['starts unfinished'][-1] or mistakes['time_format'][-1]:
                mistakes['good'].append('No')
            else:
                mistakes['good'].append('Yes')

    for i, n in mistakes['good']:
        if n == 'No':
            print(f'Something wrong with {mistakes["Name"][i]}')

            if mistakes['indexing'][i]:
                print("Indexing error")
                y = input('If you want to reindex all subs, type "y"')
                if y == 'y':
                    change_indexes(mistakes["Name"][i])
                    subs_check(path=path)

            if mistakes['time_format'][i]:
                print(f"Check its time format {mistakes['time_format'][i]}")

            if mistakes["starts unfinished"]:
                print(f"Mistake in position/finishes with/starts with")

    return mistakes


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
    with open(f'{path + folder}\\{name}', 'r', encoding='utf-8') as f:
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
        time_in_secs.append(1)

    return time_in_secs


def parse_to_sec(timestamp: str):
    """
    :param timestamp: файл в чч:мм:сс
    :return: в секундах
    """

    time = re.match(r'(\n?\d+):(\d+):(\d+),(\d+)', timestamp)
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
    mistakes = subs_check(path=path+input_folder)
    if 'No' in mistakes['good']:
        raise Exception('Needs rework')
    database = {'name': [], 'time': [], 'duration': []}
    for i in tqdm(os.listdir(path + input_folder)):
        if 'srt' in i:
            file, sr = sf.read(path + input_folder + '/' + i[:-3] + 'mp3')
            time = read_timestamps(i, folder=input_folder)
            database['name'].append(i)
            database['time'].append(time)
            database['duration'].append(len(file) / sr)

    db = pd.DataFrame(database)
    db.to_csv('Database.csv', index=False)


def database_card(db='Database.csv'):
    from datetime import datetime
    df = pd.read_csv(db)
    card = {}
    all_speech = 0
    for i in list(df.index):
        timestamps = df.loc[i, 'time']
        if timestamps[0] == '[':
            timestamps = timestamps[1:len(timestamps) - 1]
        timestamps = timestamps.split(',')
        timestamps = list(map(float, timestamps))
        starts = [timestamps[i * 3 - 3] for i in range(1, len(timestamps) // 3)]
        finishes = [timestamps[i * 3 - 2] for i in range(1, len(timestamps) // 3)]
        speech = [finishes[i] - starts[i] for i, n in enumerate(starts)]
        all_speech += sum(speech)
        card[df.loc[i, 'name']] = int(sum(speech) / df.loc[i, 'duration'] * 100)
    all_durations = sum(list(df['duration']))

    with open('database_card.md', 'a+') as file:
        file.write(f'## Log from {datetime.now()}\n\n')
        for i in list(df.index):
            file.write(f'* {df.loc[i, "name"]} is {int(card[df.loc[i, "name"]])} percent of speech  \n')
        file.write(f"Overall it's {int(all_speech / all_durations * 100)} percent speech\n\n")
        file.write("---\n\n")



database_card()
# all_srt_to_csv()

