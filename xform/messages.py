from typing import Any, Optional

__all__ = ['ErrMsg']

_err_msgs = {
    'default_faild': 'Verification failed',
    'default_required': 'This field is required',
    'default_length': 'Length must be between %s and %s',
    'default_length_qeual': 'Length must be equal to %s',
    'default_invalid': 'Invalid character',
    'min_invalid': 'The minimum value is %s',
    'max_invalid': 'A maximum of %s',
    'too_less_error': 'Array length not less than %s',
    'too_long_error': 'Length of the array over %s',
    'invalid_bool': 'Not a valid boolean',
    'invalid_datetime': '%s cannot be formatted(e.g: %s)',
    'invalid_start_date': 'Invalid time format',
    'invalid_timestamp': '%s is not a valid timestamp',
    'invalid_url': 'Not a valid URL',
    'invalid_email': 'Not a valid email address',
    'invalid_phone': 'Phone number format is incorrect',
    'invalid_idcard': 'ID is invalid',
    'invalid_username': 'The username string entered is invalid',
    'invalid_password': 'The password string entered is invalid',
    'invalid_ip': 'Invalid Ip Address',
    'invalid_json': 'Json data format error'
}


class ErrMsg:
    @classmethod
    def set_messages(cls, messages: dict) -> None:
        '''
        custom error messages

        Important: Executed before the import fields.

        :param messages: <dict> messages, see _err_msgs define
        :return:
        '''
        if messages:
            global _err_msgs
            _err_msgs.update(messages)

    @classmethod
    def get_message(cls, name: str, default: Any = None) -> Optional[str]:
        return _err_msgs.get(name, default)
