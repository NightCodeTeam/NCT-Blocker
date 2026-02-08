import logging


class RequestsMakersException(Exception):
    def __init__(self, txt):
        self.txt = txt


class OutOfTries(RequestsMakersException):
    def __init__(self, url: str):
        super().__init__(f'Out of tries to connect to {url}')


class RequestMethodNotFoundException(RequestsMakersException):
    def __init__(self, method: str):
        txt = f'Request method not found: {method}'
        logging.error(txt, 'error')
        super().__init__(txt)


class UnableToAccess(RequestsMakersException):
    def __init__(self, url: str):
        super().__init__(f'Unable to access {url}')
