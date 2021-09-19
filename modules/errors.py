class FileTooBig(Exception):
    size = 0
    maximum = 0

    def __init__(self, *, size=None, maximum=None):
        super().__init__()
        if size is not None:
            self.size = size
        if maximum is not None:
            self.maximum = maximum


class ImgurError(Exception):
    def __init__(self, *, exc_info, resp=None):
        super().__init__()
        self.exc_info = exc_info
        self.resp = resp
