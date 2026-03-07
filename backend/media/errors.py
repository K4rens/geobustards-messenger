class BadRequestError(Exception):
    def __init__(self, message: str = "invalid request"):
        super().__init__(message)
        self.message = message


class ServiceNotReadyError(Exception):
    pass
