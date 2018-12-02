#!/usr/bin/python
# coding:UTF-8
from sender import Send
from receiver import Receive

# client receive
receiver = Receive('127.0.0.1', 9999, (' ', 0), False, 10)
receiver.Start('EP03End.mp4')


# # client send
# sender = Send(' ', 0, ('127.0.0.1', 9999), False, 10)
# sender.Start("EP03End.mp4")


