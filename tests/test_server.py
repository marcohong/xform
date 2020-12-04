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


class UserSchema(schema.Schema):
    uid = fields.Integer(required=True)
    name = fields.Username(required=True, length=(4, 20))
    roles = fields.IntList(required=False)
    remark = fields.Str()


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
        order=fields.Jsonify(required=False),
        user=fields.Nested(UserSchema, required=False),
        ids=fields.IntList(min_len=0, max_len=3, required=False,
                           when_field='test', when_value=fields.Boolean.real)
    )

    async def post(self):
        # locations: if used Schema, only support json data.
        data, error = await self.form.bind(self)
        if error:
            ret = dict(code=0, state='FAIL', errors=error)
        else:
            ret = dict(code=1, state='SUCCESS', data=data)
        self.write(json.dumps(ret))


def app():
    tornado.options.parse_command_line()
    application = tornado.web.Application([(r'/', MainHandler)])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    print(f'Server running on http://localhost:{options.port}')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        print('KeyboardInterrupt, exit.')
        sys.exit(1)
