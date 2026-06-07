from typing import TYPE_CHECKING

from .csv import CsvReader
from .dwc import DwcReader
from .edf import EdfReader
from .excel import ExcelReader
from .iceberg import IcebergReader
from .mne import MneReader
from .parquet import ParquetReader
from .parquet_dir import ParquetDirReader

if TYPE_CHECKING:
    import pathlib

file_readers = {
    **{fext: CsvReader for fext in ["csv", "dat", "txt"]},
    "parquet": ParquetReader,
    "edf": EdfReader,
    **{fext: MneReader for fext in ["fif", "bdf", "gdf", "vhdr", "cnt", "set"]},
}
file_readers = {k: mod for k, mod in file_readers.items() if mod.is_available}


class FileReader:
    """Dispatches a file path to the right reader and holds it ready to load.

    Qt-free: the only GUI touchpoint, the open-file dialog in
    :meth:`user_choose_file`, imports Qt lazily. Parameter gathering (which curves,
    which index, ...) is driven externally via ``self.reader.get_params()`` -- by
    the desktop Qt adapter or the web form -- so this module stays headless-usable.
    """

    def __init__(self, filepath=None) -> None:
        self.reader = None

        filters = ";;".join(
            [f"{ext.upper()} files (*.{ext})" for ext in file_readers],
        )
        supported = " ".join(f"*.{ext}" for ext in file_readers)
        self.file_filters = f"All supported ({supported});;{filters}"
        if filepath:
            self.load_file(filepath)

    def user_choose_file(self, folder="") -> "pathlib.PurePath":
        from graphysio.dialogs import askOpenFilePath  # lazy: Qt only on desktop

        filepath, ext = askOpenFilePath(
            "Open File",
            folder=folder,
            filter=self.file_filters,
        )
        if not filepath:
            return folder
        return self.load_file(filepath)

    def load_file(self, filepath: "pathlib.PurePath") -> "pathlib.PurePath":
        ext = filepath.suffix.lstrip(".")
        if ext not in file_readers:
            raise ValueError(f"Unsupported file type: {ext}")
        self.reader = file_readers[ext]()
        self.reader.set_data({"filepath": filepath})
        # Return the parent folder for caching
        return filepath.parent

    # Meant to be executed in a separate thread (after params are gathered).
    def get_plotdata(self):
        if self.reader:
            return self.reader()
        return None


__all__ = [
    "CsvReader",
    "DwcReader",
    "EdfReader",
    "ExcelReader",
    "FileReader",
    "IcebergReader",
    "MneReader",
    "ParquetDirReader",
    "ParquetReader",
]
