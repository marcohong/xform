import abc
from typing import Any, Optional


class BaseRequest(metaclass=abc.ABCMeta):
    def __init__(self, request) -> None:
        self.request = request

    @abc.abstractmethod
    def get_argument(self,
                     name: str,
                     default: Any = None) -> Optional[str]:
        '''
        Get param from submit form.

        :param name: `<str>`
        :param default: `<str>`
        :return: `<str>`
        '''

    @abc.abstractmethod
    def get_arguments(self, name: str) -> Optional[list]:
        '''
        Get params from submit form.

        :param name: `<str>`
        :return: `<list>`
        '''

    @abc.abstractmethod
    def get_query_argument(self,
                           name: str,
                           default: Any = None) -> Optional[str]:
        '''
        Get param from query string.

        :param name: `<str>`
        :param default: `<str>`
        :return: `<str>`
        '''

    @abc.abstractmethod
    def get_query_arguments(self, name: str) -> Optional[list]:
        '''
        Get params from query string.

        :param name: `<str>`
        :return: `<list>`
        '''

    @abc.abstractmethod
    def get_from_header(self, name: str, default: Any = None) -> Optional[str]:
        '''
        Get param from headers.

        :param name: `<str>`
        :param default: `<str>`
        :return: `<str>`
        '''

    @abc.abstractmethod
    def get_from_cookie(self, name: str, default: Any = None) -> Optional[str]:
        '''
        Get param from cookies.

        :param name: `<str>`
        :param default: `<str>`
        :return: `<str>`
        '''

    @abc.abstractmethod
    def get_body(self) -> Optional[str]:
        '''
        Get request body.

        :return: `<str>`
        '''

    def translate(self, message: str) -> str:
        '''
        Translation message

        :param message: `<str>`
        :return: `<str>`
        '''
        return message

    def get_request_method(self) -> str:
        '''
        Get request method

        :return: `<str>` GET,POST,PUT,DELETE,OPTIONS(to upper)
        '''
        return 'POST'
