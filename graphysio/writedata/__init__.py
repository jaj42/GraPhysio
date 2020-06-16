from .csv import curves_to_csv
from .parquet import curves_to_parquet
from .edf import curves_to_edf
from .matlab import curves_to_matlab

curve_writers = {
    'csv': curves_to_csv,
    'edf': curves_to_edf,
    'parquet': curves_to_parquet,
    'mat': curves_to_matlab,
}
