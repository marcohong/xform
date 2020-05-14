

import os
import sys
import asyncio
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

try:
    from xform.messages import ErrMsg
    ErrMsg.set_messages({'invalid_start_date': 'time invalid'})
    from xform import fields
    from xform.form import Form
except ImportError:
    pass


class UserForm(Form):
    id = fields.Integer(required=True, _min=2)
    uname = fields.Username(required=True, length=(4, 20))
    stime = fields.StartDate(required=True)
    etime = fields.EndedDate('stime', required=True)
    roles = fields.IntList(required=False)


class TestForm:
    @classmethod
    async def test_a(cls):
        _form = UserForm()
        data = {'id': 2,
                'uname': 'hwwwh',
                'stime': '2020-01-01',
                'etime': '2021-01-01',
                'roles': [1, 2]}
        ret, error = await _form.dict_bind(data)
        print(ret)
        print('--**--' * 10)
        print(error)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TestForm.test_a())
