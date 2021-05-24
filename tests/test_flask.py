from flask import request
from flask import Flask
from xform.httputil import HttpRequest
from xform.adapters.flask import FlaskRequest
from xform.form import SubmitForm
from xform import fields
HttpRequest.configure(request_proxy=FlaskRequest)


app = Flask(__name__)

form = SubmitForm(
    id=fields.Integer(required=True, _min=1),
    name=fields.Str(required=True, length=(3, 20))
)


@app.route('/', methods=['GET', 'POST'])
async def index():
    # 注意表单之前获取过body数据可能会影响get_data取不到数据(因为缓冲区数据已被flask删除)
    data, error = await form.bind(request)
    if error:
        return {'error': error}
    return {'data': data}

if __name__ == '__main__':
    app.run(port=8888)
