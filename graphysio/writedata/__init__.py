from .csv import curves_to_csv
from .parquet import curves_to_parquet
from .edf import curves_to_edf

curve_writers = {
    'csv': curves_to_csv,
    'edf': curves_to_edf,
    'parquet': curves_to_parquet,
}
