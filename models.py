from google.appengine.ext import db

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
