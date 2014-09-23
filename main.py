#!/usr/bin/env python
# coding:utf-8
import webapp2
import handlers


app = webapp2.WSGIApplication([
    ('/', handlers.MainHandler), # list of accessed messages
    ('/my/', handlers.MyHandler), # list of my messages
    ('/info/', handlers.InfoHandler),
    ('/mess/([A-Za-z0-9\-]+)/', handlers.MessHandler),
    ('/mess/([A-Za-z0-9\-]+)/edit/', handlers.MessEditHandler),
], debug=True)
