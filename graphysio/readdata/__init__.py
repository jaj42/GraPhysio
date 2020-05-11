from .csv import CsvReader, DlgNewPlotCsv
from .parquet import ParquetReader, DlgNewPlotParquet

readers = {'csv' : CsvReader, 'parquet' : ParquetReader}
dlgNewPlots = {'csv' : DlgNewPlotCsv, 'parquet' : DlgNewPlotParquet}
