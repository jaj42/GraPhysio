from graphysio.dialogs import DlgDWCOpen
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData
from pandas.api.types import is_datetime64_any_dtype

try:
    import dwclib
except ImportError:
    is_available = False
else:
    is_available = True


class DwcReader(BaseReader):
    is_available = is_available

    def dwc_search_patient(self, patientid):
        return dwclib.read_patient(patientid=patientid)

    def askUserInput(self) -> None:
        def cb(reqdata) -> None:
            self.userdata = reqdata

        dlgchoice = DlgDWCOpen(self.dwc_search_patient)
        dlgchoice.dlgdata.connect(cb)
        dlgchoice.exec_()
        return None

    def get_plotdata(self) -> PlotData:
        if not self.userdata:
            raise ValueError("no request data")
        if self.userdata["type"] == "numerics":
            df = dwclib.read_numerics(
                patientids=self.userdata["patientid"],
                dtbegin=self.userdata["from"],
                dtend=self.userdata["to"],
                sublabels=self.userdata["items"],
            )
        elif self.userdata["type"] == "waves":
            df = dwclib.read_waves(
                patientid=self.userdata["patientid"],
                dtbegin=self.userdata["from"],
                dtend=self.userdata["to"],
                labels=self.userdata["items"],
            )
        else:
            raise ValueError("wrong data request type")

        if is_datetime64_any_dtype(df.index):
            df.index = df.index.tz_localize(None)
        df.index = df.index.astype("datetime64[ns]").astype("int")

        return PlotData(data=df, name=str(self.userdata["patientid"]))
