import os
import numpy as np
from matplotlib import pyplot as plt


def plot_corrcoef(arr1, arr2, output_dir: str = None, title: str = None, x: str = 'indicator',
                  y: str = 'Return', save_fig: bool = False):
    """
    plot_corrcoef(past_returns, future_returns, output_dir='my_favorite/1', title='comparison', save_fig=True)
    事前にnanは削っておくこと

    ::example
    a=np.vstack([arr1, arr2])
    a=a[:, ~np.isnan(a).any(axis=0)]
    print(a)

    :param x: str
    :param y: str
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

    if title is None:
        title = 'Correlation'

    # 頻出する総和を先に計算
    N = len(arr2)
    Nxy = np.sum([xi * yi for xi, yi in zip(arr1, arr2)])
    Nx = np.sum([xi for xi, yi in zip(arr1, arr2)])
    Ny = np.sum([yi for xi, yi in zip(arr1, arr2)])
    Nx2 = np.sum([xi * xi for xi, yi in zip(arr1, arr2)])

    # 係数
    a = (N * Nxy - Nx * Ny) / (N * Nx2 - Nx ** 2)
    b = (Nx2 * Ny - Nx * Nxy) / (N * Nx2 - Nx ** 2)

    # Yの誤差
    sigma_y = np.sqrt(1 / (N - 2) * np.sum([(a * xi + b - yi) ** 2 for xi, yi in zip(arr1, arr2)]))

    # 係数の誤差
    sigma_a = sigma_y * np.sqrt(N / (N * Nx2 - Nx ** 2))
    sigma_b = sigma_y * np.sqrt(Nx2 / (N * Nx2 - Nx ** 2))

    fig = plt.figure()
    fig.suptitle(title)
    ax = fig.add_subplot(111)
    ax.scatter(arr1, arr2, c="blue", s=20, edgecolors="blue", alpha=0.3)
    ax.set_xlabel(f"{x}")
    ax.set_ylabel(f"{y}")
    ax.grid(which="major", axis="x", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.grid(which="major", axis="y", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.text(1.02, 0.04,
            f"y = {a:.3f} \u00B1 {sigma_a:.3f} x + {b:.3f} \u00B1 {sigma_b:.3f}\nsigma$_y$={sigma_y:.3f}",
            transform=ax.transAxes)
    ax.text(0.83, 0.16, f"IC={correlation:.4f}", transform=ax.transAxes)
    ax.text(0.788, 0.1, f"R**2={r2:.4f}", transform=ax.transAxes)
    ax.text(0.59, 0.04, f"ProportionCorrect={(abs(correlation) + 1) / 2 * 100:.2f}%", transform=ax.transAxes)

    if save_fig:
        plt.savefig(f'{output_dir}/{title}.png')

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
