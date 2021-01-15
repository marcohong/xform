from sanic import Sanic
from sanic.response import json
from xform.httputil import HttpRequest
from xform.adapters.sanic import SanicRequest
from xform.form import SubmitForm
from xform import fields
HttpRequest.configure(request_proxy=SanicRequest)

app = Sanic('hello')

form = SubmitForm(
    id=fields.Integer(required=True, _min=1),
    name=fields.List(required=True, length=(3, 20)))


@app.route('/', methods=['GET', 'POST'])
async def test(request):
    data, error = await form.bind(request)
    if error:
        return json(error, status=400)
    return json(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
