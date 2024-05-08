from graphysio.structures import PlotData


class BaseReader:
    def __init__(self) -> None:
        self.userdata = {}

    def set_data(self, data) -> None:
        self.userdata.update(data)

    def askUserInput(self) -> None:
        pass

    def __call__(self) -> PlotData:
        raise NotImplementedError
