#### xform
表单数据绑定验证框架，支持Tornado(默认)、aiohttp、sanic，可自行扩展支持其它的python web框架

------

#### 版本要求

------

目前已支持的web框架

| Web框架          | Python版本    | 备注                           |
| ---------------- | ------------- | ------------------------------ |
| Tornado >= 6.0.0 | python >= 3.6 |                                |
| Aiohttp >= 3.6.0 | python >= 3.7 | aiohttp对python最低支持版本3.7 |
| Sanic >= 19.3    | python >= 3.6 |                                |

#### 使用示例

------

Tornado示例，更多demo请查看tests文件夹

```python
# Tornado >= 6.0.0
import json
import tornado.web
from xform import fields
from xform import schema
from xform.form import SubmitForm

class UserSchema(schema.Schema):
    uid = fields.Integer(required=True)
    name = fields.Username(required=True, length=(4, 20))

class MainHandler(tornado.web.RequestHandler):
    # when_field 当表单某一个字段的值在when_value中定义 则强制变为必填(required=True)
    # 如果表单提交类型的是json按照字典方式传值即可，否则使用user.uid=xxx方式传值
    form = SubmitForm(
        id=fields.Integer(required=True, _min=1),
        name=fields.Str(required=True),
        user=fields.Nested(UserSchema, required=False)
    )
    
    async def validate(self):
        '''
        locations:获取数据方式仅限于指定的作用域，locations可以是str或者tuple
        作用域: form/json/query/headers/cookies，组合使用例如locations=('form','json')
        data, error = await self.form.bind(self, locations='json')
        '''
        data, error = await self.form.bind(self)
        if error:
            return dict(code=0, state='FAIL', error=error)
        return dict(code=1, state='SUCCESS', data=data)

    async def post(self):
        # locations: if used Schema, only support json data.
        ret = await self.validate()
        self.write(json.dumps(ret))

    async def get(self):
        ret = await self.validate()
        self.write(json.dumps(ret))
```

自定义的提示(3种方式)

```python
'''
1.替换提示内容
'''
from xform.messages import ErrMsg
# ErrMsg.set_messages在导入fields/validator之前执行
ErrMsg.set_messages({'invalid_start_date': 'time invalid'})
from xform import fields

'''
2.使用国际化文件message.po
默认情况下是使用tornado的locale.translate('xxx')
请把messages.py定义的value翻译即可，例如:
msgid "Length must be between %s and %s" (注意%s不能少)
msgstr "长度必须在%s到%s之间"
'''
from xform import fields
# coding...

'''
3.替换提示内容，后再使用国际化，请根据第1步在导入fields/validator之前设置，
国际化文件message.po定义相对应替换后的内容即可
'''


```

demo

```bash
cd tests/
# test tornado
python3 test_tornado.py
# test aiohttp web
python3 test_aiohttp.py
# test sanic web
python3 test_sanic.py
...

```

#### 扩展组件

------

##### 自定义fields类型

```python
import re
from typing import Optional, Any
from xform.fields import Integer, Str, VALUE_TYPES
from xform.form import SubmitForm
'''
实现_validate方法即可，如果返回值需要转换则重写get_value方法
'''
class UserField(Integer):
    # 不需要转换，因为返回值是一个缓存对象
    cvt_type = None

    def add_err_msg(self) -> None:
        self.err_msg.update({'not_exist': 'User does not exist'})

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[dict]:
        data = await UserCache.get(value)
        # 错误时调用self.set_error('xxx')设置错误提示语，不需要返回内容，成功时返回内容
        if not data:
            self.set_error('not_exist')
        else:
            # 返回的是缓存对象
            return data

class OrderNOField(Str):
    regex = r'^[a-zA-Z0-9_]+$'

    def add_err_msg(self) -> None:
        self.err_msg.update({'invalid': 'Invalid order'})

    def __init__(self,
                 *,
                 length: tuple = 20,
                 **kwargs: Any):
        kwargs['length'] = length
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        ret = re.match(self.regex, value)
        if not ret:
            self.set_error('invalid')
            return
        return value

# user_id是表单提交的字段(data_key是可选的，如果为空则使用user作为表单字段)
form = SubmitForm(
    user=UserField(data_key='user_id', required=True),
    order_no=OrderNOField(required=True)
)
```

##### 自定义的validator验证

```python
from xform.fields import Str
from xform.validate import Validator, ValidationError
#参考OneOf
class OneOf(Validator):
    default_message = ErrMsg.get_message('invalid_option')

    def __init__(self, choices: Union[list, tuple], error: str = None):
        self.choices = choices
        self.error = error or self.default_message

    def __call__(self, value: Union[str, int]):
        '''
        call方法实现逻辑
        '''
        if value is None or value not in self.choices:
            # 验证错误时请抛出ValidationError错误
            raise ValidationError(self.error)
        return value

# 使用validate
form = SubmitForm(
    tag=Str(required=True, validate=OneOf(('bule', 'red', 'green')))
)
```

##### 其它web框架支持

```python
'''
Tornado为例
'''
from xform.httputil import BaseRequest
class TornadoRequest(BaseRequest):
    def __init__(self, request):
        super().__init__(request)

    def get_argument(self,
                     name: str,
                     default: Any = None) -> Optional[str]:
        return self.request.get_argument(name, default=default)

    def get_from_header(self,
                        name: str,
                        default: Any = None) -> Optional[dict]:
        return self.request.request.headers.get(name, default)

    def translate(self, message: str) -> str:
        return self.request.locale.translate(message)
    # ...实现BaseRequest里面的方法，
    # 详细实现请参考xform.adapters.tornado.TornadoRequest

# 启动web服务前设置一下xform的request代理(不设置默认Tornado)，以aiohttp为例
from xform.httputil import HttpRequest
from xform.adapters.aiohttp import AioHttpRequest
HttpRequest.configure(request_proxy=AioHttpRequest)
# Coding...
```

#### License

------

`xfrom` is offered under the MIT license.

