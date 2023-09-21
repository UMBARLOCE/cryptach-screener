from functools import lru_cache

import numba as numba
import numpy as np
import pandas as pd


def nadaraya_watson_envelope(data: pd.DataFrame, h: float = 5, mult: float = 3, length: int = 500):
    """
    Nadaraya-Watson Envelope
        close: close price,
        h: bandwidth, controls the degree of smoothness of the envelopes , with higher values returning smoother results.
        mult: multiplier, controls the envelope width
        length: determines the number of recent price observations to be used to fit the Nadaraya-Watson Estimator.
    """

    # calculate the Nadaraya-Watson envelope on the last bar
    y = np.zeros(length)

    # calculate the kernel function
    estimation = calculate_estimation(data.Close.to_numpy(), h, length, y)

    # calculate the mean absolute error
    mae = estimation / length * mult

    data['NWE_upper'] = y + mae  # upper band
    data['NWE_lower'] = y - mae  # lower band

    return data


# @numba.njit
def calculate_estimation(close_array, h, length, y):
    estimation = 0
    for i, close in enumerate(close_array):
        cumulative_weight, current_weight = calculate_nwe_weights(close_array, h, i, length)
        y2 = current_weight / cumulative_weight
        estimation += np.abs(y2 - close)
        y[i] = y2
    return estimation


# @numba.njit
def calculate_nwe_weights(close_array, h, i, length):
    current_weight = 0
    cumulative_weight = 0
    for j, close in enumerate(close_array):
        w = calculate_weight(h, i, j)
        current_weight += close * w
        cumulative_weight += w
    return cumulative_weight, current_weight


@lru_cache(maxsize=None)
@numba.njit()
def calculate_weight(h, i, j):
    return np.exp(-(np.power(i - j, 2) / (h * h * 2)))
