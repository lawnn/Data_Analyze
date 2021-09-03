from matplotlib import pyplot as plt
from numpy import corrcoef


def plot_corrcoef(dt, arr1, arr2):
    correlation = corrcoef(arr1, arr2)
    r2 = correlation[0][1] ** 2
    # グラフ出力.
    title = f"Correlation {dt:%Y}/{dt:%m}/{dt:%d}"
    fig = plt.figure()
    fig.suptitle(title)
    ax = fig.add_subplot(111)
    ax.scatter(arr1, arr2, c="blue", s=20, edgecolors="blue", alpha=0.3)
    ax.set_xlabel(f"Indicator1")
    ax.set_ylabel(f"Indicator2")
    ax.grid(which="major", axis="x", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.grid(which="major", axis="y", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
    ax.text(0.8, 0.1, f"R**2={r2:.4f}", transform=ax.transAxes)
    plt.savefig('corrcoef.png')
    plt.show()
