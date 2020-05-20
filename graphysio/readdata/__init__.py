from .csv import CsvReader
from .parquet import ParquetReader
from .edf import EdfReader

from graphysio.dialogs import askOpenFilePath

readers = {'csv': CsvReader, 'parquet': ParquetReader, 'edf': EdfReader}


class ReadFile:
    def __init__(self, caption, dircache=''):
        super().__init__()
        self.dircache = dircache
        self.caption = caption

        filters = ';;'.join(
            [f'{ext.upper()} files (*.{ext})(*.{ext})' for ext in readers]
        )
        supported = ' '.join(f'*.{ext}' for ext in readers)
        self.file_filters = f'All supported ({supported});;{filters}'

    def getdata(self) -> None:
        filepath, ext = askOpenFilePath(
            self.caption, folder=self.dircache, filter=self.file_filters
        )
        if not filepath:
            return
        reader = readers[ext]()
        data = reader(filepath)
        return data
