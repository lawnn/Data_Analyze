import os
import numpy as np
from matplotlib import pyplot as plt


def plot_corrcoef(arr1, arr2, output_dir: str = None, title: str = None, save_fig: bool = False):
    """ plot_corrcoef(past_returns, future_returns, output_dir='my_favorite/1', title='comparison', save_fig=True)
    :param arr1: ndarray
    :param arr2: ndarray
    :param output_dir: png/comparison
    :param title: EXAMPLE
    :param save_fig: True or False
    :return:
    """

    if output_dir is None:
        output_dir = f'./png/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    correlation = np.corrcoef(arr1, arr2)[1, 0]
    r2 = correlation ** 2
    # グラフ出力.
    if title is None:
        title = 'Correlation'
    fig = plt.figure()
    fig.suptitle(title)
    ax = fig.add_subplot(111)
    ax.scatter(arr1, arr2, c="blue", s=20, edgecolors="blue", alpha=0.3)
    ax.set_xlabel(f"Indicator")
    ax.set_ylabel(f"Return")
    ax.grid(which="major", axis="x", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.grid(which="major", axis="y", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.text(0.84, 0.16, f"IC={correlation:.4f}", transform=ax.transAxes)
    ax.text(0.798, 0.1, f"R**2={r2:.4f}", transform=ax.transAxes)
    ax.text(0.60, 0.04, f"ProportionCorrect={(correlation + 1) / 2 * 100:.2f}%", transform=ax.transAxes)
    if save_fig:
        plt.savefig(f'{output_dir}/{title}_corrcoef.png')
    plt.show()


def np_shift(arr, num=1, fill_value=np.nan):
    result = np.empty_like(arr)
    if num > 0:
        result[:num] = fill_value
        result[num:] = arr[:-num]
    elif num < 0:
        result[num:] = fill_value
        result[:num] = arr[-num:]
    else:
        result[:] = arr
    return result
