from graphysio.core.params import ParamSpec
from graphysio.structures import PlotData


class BaseReader:
    """Qt-free base for all file/source readers.

    Subclasses implement :meth:`get_params` (what inputs are needed, given the
    current ``userdata``) and :meth:`__call__` (the actual, pure-pandas load). The
    interaction layer -- Qt dialogs on the desktop, an HTTP form on the web --
    collects answers and feeds them back via :meth:`set_data`.
    """

    is_available = True

    def __init__(self) -> None:
        self.userdata: dict = {}

    def set_data(self, data: dict) -> None:
        self.userdata.update(data)

    def get_params(self) -> list[ParamSpec]:
        """Inputs still needed to load, given current ``userdata``.

        Return ``[]`` when the reader has everything it needs. May read the file or
        its metadata to populate choices. Must not import any GUI toolkit. Called
        repeatedly to support multi-stage prompting.
        """
        return []

    def __call__(self) -> PlotData | list[PlotData] | None:
        raise NotImplementedError

    # Back-compat alias: the desktop (mainui, FileReader) schedules ``get_plotdata``.
    def get_plotdata(self) -> PlotData | list[PlotData] | None:
        return self()
