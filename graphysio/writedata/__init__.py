from .csv import curves_to_csv
from .edf import curves_to_edf
from .matlab import curves_to_matlab
from .parquet import curves_to_parquet

curve_writers = {
    'csv': curves_to_csv,
    'edf': curves_to_edf,
    'parquet': curves_to_parquet,
    'mat': curves_to_matlab,
}
