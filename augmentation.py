import numpy as np
import librosa as lr
import soundfile as sf
import os
import pandas as pd
from os.path import splitext


def code_markers(markers, sr):
    """
    Take mask and turn it into timestamps
    :param markers: array of 1s and 0s
    :param sr: sample rate
    :return: timestamps and 1 as a separator
    """

    markers = np.array(markers)
    i = 1
    res = []

    while i < markers.shape[0]:

        if markers[i - 1] != 0 and i == 1:
            # If starts with a sub right away
            res.append(0.0)

        elif markers[markers.shape[0] - 1] != 0 and i == markers.shape[0] - 1:
            # If ends on a sub
            res.append(markers.shape[0] / sr)
            res.append(int(markers[i]))

        elif markers[i - 1] != markers[i]:
            if markers[i] == 1:
                # If prev char is not equal to current 1
                # we mark it as a start of a sub
                res.append(i / sr)
            elif markers[i] == 0:
                # If prev char is not equal to current 0
                # we mark it as an end of a sub
                res.append(i / sr)
                res.append(int(markers[i - 1]))
        i += 1

    return res


def move_audio(name: str, sr: int, sec: float):
    audio, sr = lr.load(name, sr)
    if sec > 0:
        zeros = np.zeros(int(sec * sr))
        audio = np.hstack((zeros, audio))
    else:
        audio = audio[int(sr * abs(sec)):]
    n_name, ext = splitext(name)
    sf.write(n_name + '_' + str(sec) + ext, audio, sr)


def move_db(db: str, sec: float, path='Mono/'):
    df = pd.read_csv(db)

    # df = df.drop(columns=['Unnamed: 0'])
    files = os.listdir(path)
    for i in (list(df.index)):
        audio_n = df.loc[i, 'Name']
        if audio_n in files:
            name, ext = splitext(audio_n)
            move_audio(path + audio_n, 16000, sec)
            mask = df.loc[i, 'Markers']
            if mask[0] == '[': mask = mask[1:len(mask) - 1]
            mask = mask.split(',')
            mask = list(map(float, mask))
            for j in range(len(mask)):
                if j % 3 != 2:
                    mask[j] += sec
                    mask[j] = round(mask[j], 4)
            mask = str(mask)
            mask = mask[1:(len(mask) - 1)]
            df.loc[i + len(list(df.index)), 'Name'] = name + '_' + str(sec) + ext
            df.loc[i + len(list(df.index)) - 1, 'Markers'] = str(mask)

    df.reset_index(drop=True)
    new_df = df
    name, ext = splitext(db)
    new_df.to_csv(name + '+' + str(sec) + ext, index=False)
