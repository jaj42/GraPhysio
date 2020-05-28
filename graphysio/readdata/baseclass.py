from graphysio.structures import PlotData


class BaseReader:
    def __init__(self):
        self.userdata = {}

    def set_data(self, data):
        self.userdata.update(data)

    def askUserInput(self):
        pass

    def __call__(self) -> PlotData:
        raise NotImplementedError
