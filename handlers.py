import jinja2
import os
from google.appengine.api import users
from cgi import escape
import webapp2
from google.appengine.api.users import User

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
        title = self.request.get('mess-title')
        content = self.request.get('mess-text')
        access_list = self.request.get('mess-acc').split(', ')
        access_list = [User(email=email).key for email in access_list]
        mess = Message(title=title, user=self.user, content=content, access_list=access_list)
        mess.put()
        self.redirect('/')


class InboxHandler(BaseHandler):
    def get(self):
        """ show list of inbox user messages """
        self.render('inbox')

    def post(self):
        """ post answer message """
        title = self.request.get('mess-title')
        content = self.request.get('mess-text')
        parent_mess = self.request.get('mess-parent')
        parent_mess = Message.getone(parent_mess)
        access_list = self.request.get('mess-acc').split(', ')
        access_list = [User(email=email).key for email in access_list]
        mess = Message(title=title, user=self.user, content=content, access_list=access_list, parent_mess=parent_mess)
        mess.put()
        self.redirect('/')

class MessHandler(BaseHandler):
    def get(self, mess_key):
        """ show message """
        mess_key = escape(mess_key)
        mess = Message.getone(mess_key)
        if mess.can_read(self.user):
            self.render('mess', {'mess': mess})
        else:
            self.redirect('/')


class MessEditHandler(BaseHandler):
    def get(self, mess_key):
        """ show message editor """
        mess_key = escape(mess_key)
        mess = Message.getone(mess_key)
        if mess.author == self.user:
            self.render('mess_edit', {'mess': mess})
        else:
            self.redirect('/')

    def post(self, mess_key):
        """ update message """
        mess_key = escape(mess_key)
        mess = Message.getone(mess_key)
        mess.title = self.request.get('mess-title')
        mess.content = self.request.get('mess-text')
        access_list = self.request.get('mess-acc').split(', ')
        mess.access_list = [User(email=email).key for email in access_list]
        mess.put()
        self.redirect('/')