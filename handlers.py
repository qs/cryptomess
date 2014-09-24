import jinja2
import os
from google.appengine.api import users
from cgi import escape
import webapp2

from models import Message

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class BaseHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.user = users.get_current_user()

    def render(self, tpl_file, tvals={}):
        tvals['user'] = self.user
        tvals['logout'] = users.create_logout_url("/")
        tpl = jinja_environment.get_template('templates/' + tpl_file + '.html')
        self.response.out.write(tpl.render(tvals))


class MainHandler(BaseHandler):
    def get(self):
        """ show list of user messages """
        self.render('main')

    def post(self):
        """ post new message """


class InboxHandler(BaseHandler):
    def get(self):
        """ show list of inbox user messages """
        self.render('inbox')

    def post(self):
        """ post answer message """


class MessHandler(BaseHandler):
    def get(self, mess_key):
        """ show message """
        mess_key = escape(mess_key)
        mess = Message.getone(mess_key)
        self.render('mess', {'mess': mess})


class MessEditHandler(BaseHandler):
    def get(self):
        """ show message editor """

    def post(self):
        """ update message """