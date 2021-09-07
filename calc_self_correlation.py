from matplotlib import pyplot as plt
import numpy as np


def plot_corrcoef(arr1, arr2):
    correlation = np.corrcoef(arr1, arr2)
    r2 = correlation[0][1] ** 2
    # グラフ出力.
    title = f"IC = {correlation[0][1]:.4f}"
    fig = plt.figure()
    fig.suptitle(title)
    ax = fig.add_subplot(111)
    ax.scatter(arr1, arr2, c="blue", s=20, edgecolors="blue", alpha=0.3)
    ax.set_xlabel(f"Indicator1")
    ax.set_ylabel(f"Indicator2")
    ax.grid(which="major", axis="x", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.grid(which="major", axis="y", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.text(0.75, 0.1, f"R**2={r2:.4f}", transform=ax.transAxes)
    ax.text(0.55, 0.04, f"ProportionCorrect={(correlation[0][1] + 1) / 2:.2f}%", transform=ax.transAxes)
    plt.savefig('corrcoef.png')
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
