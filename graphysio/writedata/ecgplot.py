from typing import List

import pandas as pd

from graphysio.plotwidgets.curves import CurveItem

import ecg_plot


def export_curves(
    curves: List[CurveItem],
    filepath: str,
    index_label: str = "timens",
) -> None:
    sers = [c.series for c in curves]
    names = [c.name() for c in curves]
    data = pd.concat(sers, axis=1).sort_index()
    # TODO: resample
    ecg = data.to_numpy()
    ecg = ecg.T
    ecg_plot.plot(
        ecg, sample_rate=500, title=filepath.stem, lead_index=names, columns=1
    )
    ecg_plot.save_as_png(filepath.stem, f"{filepath.parent}/")


export_curves.is_available = True
