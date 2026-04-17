# backend/visualize.py

import os
import matplotlib.pyplot as plt


def save_heatmap(heatmap, output_path):
    """
    Save GradCAM heatmap
    """

    plt.imshow(heatmap, cmap="jet")
    plt.axis("off")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
    plt.close()

    return output_path