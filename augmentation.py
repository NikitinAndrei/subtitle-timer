import numpy as np
import librosa as lr
import soundfile as sf
import os
import pandas as pd
from os.path import splitext


def code_markers(markers, sr):
    """
    Take a mask and turn it into timestamps
    :param markers: array of 1s and 0s
    :param sr: sample rate
    :return: timestamps and 1 as a separator
    """
    markers += [0]  # 1 zero at the end does nothing to the arrow, but works as an end marker
    var = 0
    res = []
    for i, n in enumerate(markers):
        char = n
        if char != var:
            if var == 0:
                res.append(i / sr)
            elif var == 1 or var == 2:
                res.append(i / sr)
                res.append(var)
        var = n
    return res


def move_audio(name: str, sr: int, sec: float):
    """

    :param name: name of an audio
    :param sr: sample rate
    :param sec: seconds you want an audio to move
    """
    audio, sr = lr.load(name, sr)

    if sec >= 0:
        zeros = np.zeros(int(sec * sr))
        audio = np.hstack((zeros, audio))
    else:
        audio = audio[int(sr * abs(sec)):]
    n_name, ext = splitext(name)
    sf.write(n_name + '_' + str(sec) + ext, audio, sr)


def move_db(db: str, sec: float, path='Mono/'):
    """
    Moves audio and corresponding timestamps
    :param db: Database file
    :param sec: seconds for audio and it's markers to move
    :param path: path of the audios

    """
    df = pd.read_csv(db)
    # Comment below for dropping index column
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


def decode_markers(mask, sr=16000):
    end = np.array([])
    if mask[0] == '[':
        mask = mask[1:len(mask) - 1]
    mask = mask.split(',')
    mask = list(map(float, mask))

    s_zeros = np.zeros(int(mask[0] * sr))
    end = np.hstack((s_zeros, end))

    for i in range(1, int(len(mask) / 3)):
        a = np.ones(int((mask[i * 3 - 2] - mask[i * 3 - 3]) * sr), dtype='uint8') * mask[i * 3 - 1]
        b = np.zeros(int((mask[i * 3] - mask[i * 3 - 2]) * sr), dtype='uint8')
        end = np.hstack((end, a, b))

    last = np.ones(int((mask[-2] - mask[-3]) * sr) + 1) * mask[-1]
    end = np.hstack((end, last))
    return end


def ohe(file):
    """
    one-hot encode in 3 classes. That's not good for two classes

    """
    cont = np.zeros((file.shape[0], file.shape[1], classes))
    np.place(cont[:, :, 0], file[:, :] == 0, 1)
    np.place(cont[:, :, 1], file[:, :] == 0, 0)
    np.place(cont[:, :, 2], file[:, :] == 0, 0)

    np.place(cont[:, :, 0], file[:, :] == 1, 0)
    np.place(cont[:, :, 1], file[:, :] == 1, 1)
    np.place(cont[:, :, 2], file[:, :] == 1, 0)

    np.place(cont[:, :, 0], file[:, :] == 2, 0)
    np.place(cont[:, :, 1], file[:, :] == 2, 0)
    np.place(cont[:, :, 2], file[:, :] == 2, 1)

    return cont


def keras_generator(df,
                    batch_size,
                    t,
                    path='Mono/',
                    sr=16000):
    """

    :param df: dataframe to make masks from
    :param batch_size: how many records for a batch to pass
    :param t: duration of an audio recording
    :param path: path to the database
    :param sr: sample rate
    :return: one-hot encoded timestamps of audio files
    """
    files = os.listdir(path)
    x_batch = np.empty(sr * t)
    y_batch = np.empty(sr * t)
    inds = list(df.index)
    toggle = 0
    j = 0
    for i in range(batch_size):

        k = inds[j]
        if df.loc[k, 'Name'] in files:

            f_n = path + df.loc[k, 'Name']  # file name
            f_m = df.loc[k, 'Markers']  # file of mask
            file, o = lr.load(f_n, sr)  # o - sample rate as well

            # Нормировка
            file = file / np.amax(abs(file))
            # Декодим маску
            mask = decode_markers(f_m)
            # Файл меньше длины окна разбиения (spoiler_alert: always)
            if len(file) < sr * t:

                # Дополняем нулями до размеров окна srt
                sub_file = np.hstack((file,
                                      np.zeros(sr * t - len(file))))
                # Декод маски
                sub_mask = np.hstack((mask,
                                      np.zeros(sr * t - len(mask))))

                # Первый батч
                if toggle == 0:
                    x_batch[:] = sub_file[:]
                    y_batch[:] = sub_mask[:]
                    toggle += 1
            # Файл больше или равен длины
            else:
                # Выясняем количество разбиений
                f_amount = len(file) // (sr * t)

                # Если целочисленно не поделилось, то добиваем, чтобы делилось
                if len(file) % (sr * t) != 0:
                    f_amount += 1
                    new_dur = f_amount * sr * t
                    # add zeros to fill the gap to the end
                    file = np.hstack((file, np.zeros(new_dur - len(file))))
                    mask = np.hstack((mask, np.zeros(new_dur - len(mask))))

                # Первый кусок
                sub_file = file[(0 * sr * t):(1 * sr * t)]
                sub_mask = mask[(0 * sr * t):(1 * sr * t)]

                # Первый батч
                if toggle == 0:
                    x_batch = sub_file
                    y_batch = sub_mask
                    toggle += 1

                # бьём на отдельные куски
                for part in range(2, f_amount + 1):
                    # Прибавляемый шаг
                    step = file[((part - 1) * sr * t):(part * sr * t)]
                    sub_file = np.vstack((sub_file, step))

                    # Соответствующие куски маски
                    _mask = mask[((part - 1) * sr * t):(part * sr * t)]
                    sub_mask = np.vstack((sub_mask, _mask))

            if i > 0 and np.any(x_batch) and type(sub_file) == np.ndarray:
                # Стакаем с другими файлами
                x_batch = np.vstack((x_batch, sub_file))
                y_batch = np.vstack((y_batch, sub_mask))
            j += 1

            # Кодируем, чтоб быстрее to_categorical
    y_batch = ohe(y_batch, 3)

    return x_batch, y_batch

#
# x_train, y_train = keras_generator(train_df, len(list(train_df.index)), t, sr=sr,
#                                    path='drive/MyDrive/Mono/')
#
# # # # x_val, y_val = keras_generator(val_df, len(list(val_df.index)) , t, sr=sr,
# # # #                                path='drive/MyDrive/Mono/')
#
# x_train, x_val, y_train, y_val = train_test_split(x_train,
#                                                   y_train,
#                                                   test_size=0.2,
#                                                   # random_state=0,
#                                                   shuffle=False)
