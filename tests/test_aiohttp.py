from aiohttp import web
from xform.httputil import HttpRequest
from xform.adapters.aiohttp import AioHttpRequest
from xform.form import SubmitForm
from xform import fields
HttpRequest.configure(request_proxy=AioHttpRequest)

'''
test command
curl http://localhost:8888?id=2\&name=aiohttp
curl http://localhost:8888 -X POST -d "id=2&name=aiohttp"
'''


form = SubmitForm(
    id=fields.Integer(required=True, _min=1),
    name=fields.Str(required=True, length=(3, 20)))


async def handle(request):
    data, error = await form.bind(request)
    if error:
        return web.json_response(data=error, status=400)
    return web.json_response(data=data)


app = web.Application()
app.add_routes([web.get('/', handle), web.post('/', handle)])

if __name__ == '__main__':
    web.run_app(app, port=8888)
