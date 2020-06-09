from typing import Union
from .messages import ErrMsg


class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class Validator:
    def __repr__(self):
        args = self.__repr_args__()
        args = '{}'.format(args) if args else ''

    def __repr_args__(self):
        return ''


class OneOf(Validator):
    default_message = ErrMsg.get_message('invalid_option')

    def __init__(self, choices: Union[list, tuple], error: str = None):
        self.choices = choices
        self.error = error or self.default_message

    def __call__(self, value: Union[str, int]):
        if value is None or value not in self.choices:
            raise ValidationError(self.error)
        return value
