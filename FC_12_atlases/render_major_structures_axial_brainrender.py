import random
import numpy as np
from brainrender import Scene, settings

if __name__ == "__main__":
    # ✅ settings before scene creation
    settings.DEFAULT_ATLAS = "allen_mouse_10um"
    settings.SHOW_AXES = False


    screenshot_folder = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/figures"

    Atlas_12_ROIs = [
        "Isocortex",
        "OLF",
        "HPF",
        "CTXsp",
        "STR",
        "PAL",
        "TH",
        "HY",
        "MB",
        "P",
        "MY",
        "CB",

    ]
    # ✅ add brain region
    for structure in Atlas_12_ROIs:
        scene = Scene(
            inset=False,
            title=None,
            screenshots_folder=screenshot_folder,
        )
        brain_str = scene.add_brain_region(structure, alpha=0.7)

        # ✅ root brain — transparent with clean appearance
        scene.root.mesh.alpha(0.3)
        scene.root.mesh.color("white")

        # ✅ first render to establish camera direction
        scene.render(interactive=False, camera="top", zoom=1)

        # ✅ silhouette after render so camera direction is known
        sil = scene.root.mesh.silhouette()
        sil.color("black")
        sil.lw(2)
        scene.add(sil)

        # ✅ final interactive render
        scene.render(interactive=False, camera="top", zoom=1)

        # screenshot
        scene.screenshot(name=f"{screenshot_folder}/{structure}_shot.png", scale=2)
        scene.close()