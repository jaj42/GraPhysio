from .csv import curves_to_csv
from .edf import curves_to_edf
from .matlab import curves_to_matlab
from .parquet import export_curves

curve_writers = {
    "csv": curves_to_csv,
    "edf": curves_to_edf,
    "parquet": export_curves,
    "mat": curves_to_matlab,
}

curve_writers = {k: f for k, f in curve_writers.items() if f.is_available}
