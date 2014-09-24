from google.appengine.ext import ndb


ACCESS_NONE = 0
ACCESS_LIST = 1
ACCESS_LINK = 2


class BaseModel(ndb.Model):
    @classmethod
    def getone(c, key_name):
        k = ndb.Key(c, key_name)
        return k.get()

    @property
    def id(self):
        return self.key.id()


class Message(BaseModel):
    author = ndb.UserProperty(required=True)
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    dt = ndb.DateTimeProperty(auto_now_add=True)
    access = ndb.IntegerProperty(required=True, default=ACCESS_NONE, choices=[
        ACCESS_NONE,
        ACCESS_LIST,
        ACCESS_LINK
    ])
    access_list = ndb.UserProperty(repeated=True)
    parent_mess = ndb.KeyProperty()  # parent message

    def can_read(self, user):
        if self.access == ACCESS_NONE:
            if user != self.author:
                return False
            else:
                return True
        elif self.access == ACCESS_LIST:
            if user.key in self.access_list:
                return True
            else:
                return False

    @classmethod
    def get_my_messes(cls, user):
        messes = Message.query(Message.author==user).order(-Message.dt)
        return messes

    @classmethod
    def get_inbox_messes(cls, user):
        messes = Message.query(Message.access_list.IN([user.key, ])).order(-Message.dt)
        return messes