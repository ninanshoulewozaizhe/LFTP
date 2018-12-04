#!/usr/bin/python
# coding:UTF-8
from sender import Send
from receiver import Receive
from constant import const
import sys

# data : 'LFTP lget myserver mylargefile'
# data : 'LFTP lsend myserver mylargefile'

# client receive
if sys.argv[2] == 'lget':
    receiver = Receive(sys.argv[3], const.PORT, (' ', 0), False, 10)
    receiver.Start(sys.argv[4])
else:
    sender = Send(' ', 0, (sys.argv[3], const.PORT), False, 10)
    sender.Start(sys.argv[4])
