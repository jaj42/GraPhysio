from .csv import CsvReader, DlgNewPlotCsv
from .parquet import ParquetReader, DlgNewPlotParquet
from .edf import EdfReader, DlgNewPlotEdf

readers = {'csv': CsvReader, 'parquet': ParquetReader, 'edf': EdfReader}
dlgNewPlots = {'csv': DlgNewPlotCsv, 'parquet': DlgNewPlotParquet, 'edf': DlgNewPlotEdf}
