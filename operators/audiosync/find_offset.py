"""
This code is an adaptation of 'audio-offset-finder' by BBC
"""
import os
import warnings
import numpy as np
from scipy.io import wavfile

from .mfcc import mfcc
from .convert_and_trim import convert_and_trim
from .std_mfcc import std_mfcc
from .cross_correlation import cross_correlation
from .ensure_non_zero import ensure_non_zero


def find_offset(file1, file2, freq=8000, trim=60*15, correl_nframes=1000):
    """
    Determine the offset (in seconds) between 2 audio files

    Uses cross-correlation of standardised Mel-Frequency Cepstral
    Coefficients
    """
    file1 = os.path.abspath(file1)
    file2 = os.path.abspath(file2)

    wav1_path = convert_and_trim(file1, freq, trim)
    wav2_path = convert_and_trim(file2, freq, trim)

    rate1, data1 = wavfile.read(wav1_path, mmap=True)
    data1 = data1 / (2.0 ** 15)

    rate2, data2 = wavfile.read(wav2_path, mmap=True)
    data2 = data2 / (2.0 ** 15)

    data1 = ensure_non_zero(data1)
    data2 = ensure_non_zero(data2)

    mfcc1 = mfcc(data1, nwin=256, nfft=512, fs=freq, nceps=13)[0]
    mfcc2 = mfcc(data2, nwin=256, nfft=512, fs=freq, nceps=13)[0]

    mfcc1 = std_mfcc(mfcc1)
    mfcc2 = std_mfcc(mfcc2)

    frames1 = mfcc1.shape[0]
    frames2 = mfcc2.shape[0]

    if frames1 > frames2:
        flip = 1

    else:
        flip = -1
        mfcc1, mfcc2 = mfcc2, mfcc1

    c = cross_correlation(mfcc1, mfcc2, nframes=correl_nframes)
    try:
        c.any()
    except AttributeError:
        os.remove(wav1_path)
        os.remove(wav2_path)

        return 0, 0

    max_k_index = np.argmax(c)

    offset = max_k_index * 160.0 / float(freq)
    score = (c[max_k_index] - np.mean(c)) / np.std(c)

    os.remove(wav1_path)
    os.remove(wav2_path)

    return offset * flip, score
