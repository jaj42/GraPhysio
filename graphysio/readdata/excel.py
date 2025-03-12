import pandas as pd
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData
import importlib.util

if importlib.util.find_spec("python_calamine") is None:
    is_available = False
else:
    is_available = True


class ExcelReader(BaseReader):
    is_available = is_available

    def askUserInput(self) -> None:
        return None

    def __call__(self) -> PlotData:
        filepath = str(self.userdata["filepath"])
        df = pd.read_excel(filepath, engine="calamine")
        return PlotData(data=df, filepath=filepath)
