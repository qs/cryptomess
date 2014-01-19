#!/usr/bin/env python
# coding:utf-8

import webapp2
from google.appengine.ext import db
import jinja2
import os
from cgi import escape
from google.appengine.api import users
from Crypto.Cipher import AES
from Crypto import Random
import base64
import hashlib
from google.appengine.api import mail

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Message(db.Model):
    user = db.UserProperty(required=True)
    title = db.StringProperty()
    dt = db.DateTimeProperty(auto_now_add=True)
    #content = db.ByteStringProperty(required=True)
    content = db.BlobProperty(required=True)

    @property
    def users(self):
        return AccessList.gql("WHERE messages = :1", self.key())

    def has_access(self, user):
        if user == self.user:
            return True
        al = AccessList.gql("WHERE user=:1", user).get()
        if self.key() in al.messages:
            return True
        else:
            return False


class AccessList(db.Model):
    user = db.UserProperty(required=True)
    messages = db.ListProperty(db.Key)

    def add_access(self, message):
        self.messages.append(message.key())
        self.save()

    def remove_access(self, message):
        self.messages.remove(message.key())
        self.save()


class BaseHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.user = users.get_current_user()

    def render(self, tpl_file, tvals={}):
        tvals['user'] = self.user
        tvals['logout'] = users.create_logout_url("/")
        tpl = jinja_environment.get_template('templates/' + tpl_file + '.html')
        self.response.out.write(tpl.render(tvals))

    def get_message(self, mess_id):
        mess = Message.gql("WHERE __key__ = :1", db.Key(mess_id)).get()
        if mess and mess.has_access(self.user):
            return mess
        else:
            return None

    def encypt_message(self, content, key):
        key = hashlib.sha256(key.encode("utf-8")).digest()
        content = content.encode("utf-8")
        content += ''.join([" " for i in range(16 - (len(content) % 16))])
        obj = AES.new(key, AES.MODE_ECB)
        ciphertext = obj.encrypt(content)
        return ciphertext

    def decrypt_message(self, mess, key):
        key = hashlib.sha256(key.encode("utf-8")).digest()
        obj = AES.new(key, AES.MODE_ECB)
        decrypt = obj.decrypt(mess.content)
        try:
            cont = decrypt.decode("utf-8")
            success = True
        except:
            cont = u'''Maybe the key doesn't fit. <a href="/mess/%s/">Try again</a>''' % mess.key()
            success = False
        return cont, success

    def _add_access(self, mess, access_emails):
        if access_emails != [u'']:
            for email in access_emails:
                user = users.User(email)
                if user not in mess.users:
                    message = mail.EmailMessage()
                    message.sender = self.user.email()
                    message.to = user.email()
                    message.subject = u"You have a new access at CryptoMess"
                    message.body = u"So chek it out http://cryptomess.appspot.com/"
                    message.send()
                    al = AccessList.gql("WHERE user=:1", user).get()
                    if al:
                        al.add_access(mess)
                    else:
                        al = AccessList(user=user, messages=[mess.key()])
                        al.put()

    def _upd_access(self, mess, access_emails):
        for u in mess.users:
            if u.user.email() not in access_emails:
                al = AccessList.gql("WHERE user=:1", u.user).get()
                if al:
                    al.remove_access(mess)
        self._add_access(mess, access_emails)

    def _post_mess(self):
        if self.request.get('add-mess') and self.request.get('mess-key'):
            title = self.request.get('mess-title')
            content = self.request.get('mess-text')
            key = self.request.get('mess-key')
            ciphertext = self.encypt_message(content, key)
            mess = Message(title=title, user=self.user, content=ciphertext)
            mess.put()
            self._add_access(mess, self.request.get('mess-acc').split(','))
        self.redirect('/my/')


class MainHandler(BaseHandler):
    def get(self):

        al = AccessList.gql("WHERE user = :1", self.user).get()
        if al:
            messages = Message.gql("WHERE __key__ IN :1 ORDER BY dt DESC", al.messages)
        else:
            messages = []
        self.render('main', {'messages': messages})

    def post(self):
        self._post_mess()


class MyHandler(BaseHandler):
    def get(self):
        messages = Message.gql("WHERE user = :1 ORDER BY dt DESC", self.user)
        self.render('my', {'messages': messages})

    def post(self):
        self._post_mess()


class InfoHandler(BaseHandler):
    def get(self):
        self.render('info')


class MessHandler(BaseHandler):
    def get(self, mess_id):
        mess = self.get_message(mess_id)
        if not mess:
            self.redirect('/my/')
        else:
            self.render('mess_access', {'message': mess})

    def post(self, mess_id):
        # read mess
        if self.request.get('read-mess') and self.request.get('mess-key'):
            mess = self.get_message(mess_id)
            if not mess:
                self.redirect('/my/')
            else:
                content, success = self.decrypt_message(mess, self.request.get('mess-key'))
                content = content.replace("\n", "<br />")
                self.render('mess_read', {'message': mess, 'content': content})
        else:
            self.redirect('/my/')


class MessEditHandler(BaseHandler):
    def get(self, mess_id):
        mess = self.get_message(mess_id)
        self.render('mess_access', {'message': mess})

    def post(self, mess_id):
        # edit mess
        if self.request.get('read-mess') and self.request.get('mess-key'):
            mess = self.get_message(mess_id)
            if not mess:
                self.redirect('/my/')
            else:
                content, success = self.decrypt_message(mess, self.request.get('mess-key'))
                if success:
                    m_access = ','.join([al.user.email() for al in mess.users])
                    self.render('mess_edit', {'message': mess,
                                              'content': content,
                                              'm_key': self.request.get('mess-key'),
                                              'm_access': m_access})
                else:
                    self.redirect('/mess/%s/edit/' % mess.key())
        elif self.request.get('del-mess') and self.request.get('cur-mess-key'):
            mess = self.get_message(mess_id)
            if not mess:
                self.redirect('/my/')
            else:
                content, success = self.decrypt_message(mess, self.request.get('cur-mess-key'))
                if success:
                    for al in mess.users:
                        al.remove_access(mess)
                    mess.delete()
                self.redirect('/my/')
        elif self.request.get('upd-mess') and self.request.get('cur-mess-key'):
            mess = self.get_message(mess_id)
            if not mess:
                self.redirect('/my/')
            else:
                content, success = self.decrypt_message(mess, self.request.get('cur-mess-key'))
                if success:
                    mess.title = self.request.get('mess-title')
                    self._upd_access(mess, self.request.get('mess-acc').split(','))
                    new_key = self.request.get('mess-key')
                    new_content = self.request.get('mess-text')
                    mess.content = self.encypt_message(new_content, new_key)
                    mess.save()
                    self.redirect('/my/')
                else:
                    self.redirect('/mess/%s/edit' % mess.key())
        else:
            self.redirect('/my/')


app = webapp2.WSGIApplication([
    ('/', MainHandler), # list of accessed messages
    ('/my/', MyHandler), # list of my messages
    ('/info/', InfoHandler),
    ('/mess/([A-Za-z0-9\-]+)/', MessHandler),
    ('/mess/([A-Za-z0-9\-]+)/edit/', MessEditHandler),
], debug=True)
