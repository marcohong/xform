import sys
import datetime
import json
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
from tornado.options import define, options

from xform import fields
from xform.form import SubmitForm
from xform import schema
from xform.validate import OneOf

define('port', default=8888, help='run on the given port', type=int)


'''
test command
curl http://localhost:8888?id=2\&status=1\&user.name=user1\&user.uid=100
curl http://localhost:8888 -X POST -d "id=2&status=1&user.name=user&user.uid=9"
'''


class UserSchema(schema.Schema):
    uid = fields.Integer(required=True)
    name = fields.Username(required=True, length=(4, 20))


def get_now_date() -> str:
    '''return date str'''
    return datetime.datetime.now().strftime('%Y-%m-%d')


class MainHandler(tornado.web.RequestHandler):
    form = SubmitForm(
        id=fields.Integer(required=True, _min=2),
        text=fields.EnStr(data_key='search', required=False),
        test=fields.Boolean(required=False, default=True),
        status=fields.Integer(required=True, validate=OneOf((1, 2))),
        stime=fields.StartDate(required=False, default=get_now_date),
        etime=fields.EndedDate('stime', default=get_now_date),
        user=fields.Nested(UserSchema, required=False),
        ids=fields.IntList(min_len=0, max_len=3, required=False,
                           when_field='test', when_value=fields.Boolean.real)
    )

    async def validate(self):
        data, error = await self.form.bind(self)
        if error:
            return self.write(json.dumps({'state': 'FAIL', 'error': error}))
        return self.write(json.dumps({'state': 'SUCCESS', 'data': data}))

    async def post(self):
        return await self.validate()

    async def get(self):
        return await self.validate()


def app():
    tornado.options.parse_command_line()
    application = tornado.web.Application([(r'/', MainHandler)])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    print(f'Server running on http://localhost:{options.port}')
    print('(Press CTRL+C to quit)')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(1)
