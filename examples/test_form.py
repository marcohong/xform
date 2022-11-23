import asyncio

# set_messages before import fields
# from xform.messages import ErrMsg
# ErrMsg.set_messages({'invalid_start_date': 'time invalid'})
from xform.form import Form
from xform import fields
from xform.schema import Schema


class AliasSchema(Schema):
    id = fields.Integer(required=True, _min=1)
    alias = fields.Str(required=True)


class GroupSchema(Schema):
    id = fields.Integer(required=True, _min=2)
    name = fields.Str(required=True)
    alias = fields.Nested(AliasSchema, required=False)


class UserForm(Form):
    id = fields.Integer(required=True, _min=2, _max=99)
    uname = fields.Username(required=True, length=(4, 20))
    stime = fields.StartDate(required=True)
    etime = fields.EndedDate('stime', required=True)
    roles = fields.IntList(required=True)
    group = fields.Nested(GroupSchema, required=False)


class ManagerForm(UserForm):
    mid = fields.Integer(required=True, _min=1)


class TestForm:
    @classmethod
    async def test_a(cls):
        _form = ManagerForm()
        data = {'id': 5,
                'mid': 100,
                'uname': 'tester',
                'stime': '2020-01-01',
                'etime': '2021-01-01',
                'roles': [1, 2],
                'group': {
                    'id': 10,
                    'name': 'hello',
                    'alias': {
                        'id': 1,
                        'alias': 'world'
                        }
                    }
                }
        ret, error = await _form.dict_bind(data)
        print(ret)
        print('--**--' * 10)
        print(error)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TestForm.test_a())
