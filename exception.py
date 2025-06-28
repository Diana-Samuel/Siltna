class Error(Exception):
    pass

class UploadError(Error):
    def __init__(self, exception):
        self.Exception = exception