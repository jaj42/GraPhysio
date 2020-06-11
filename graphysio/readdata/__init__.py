from .csv import CsvReader
from .parquet import ParquetReader
from .edf import EdfReader

from graphysio.dialogs import askOpenFilePath

file_readers = {'csv': CsvReader, 'parquet': ParquetReader, 'edf': EdfReader}


class FileReader:
    def __init__(self):
        super().__init__()
        self.reader = None

        filters = ';;'.join(
            [f'{ext.upper()} files (*.{ext})(*.{ext})' for ext in file_readers]
        )
        supported = ' '.join(f'*.{ext}' for ext in file_readers)
        self.file_filters = f'All supported ({supported});;{filters}'

    def askFile(self, folder='') -> 'pathlib.PurePath':
        filepath, ext = askOpenFilePath(
            'Open File', folder=folder, filter=self.file_filters
        )
        if not filepath:
            return
        self.reader = file_readers[ext]()
        self.reader.set_data({'filepath': filepath})
        self.reader.askUserInput()
        # Return the parent folder for caching
        return filepath.parent

    # Meant to be executed in seperate thread
    def get_plotdata(self) -> 'PlotData':
        if self.reader:
            return self.reader()
        else:
            return None
