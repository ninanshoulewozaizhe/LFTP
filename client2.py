from sender import Send
from receiver import Receive

# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.sendto(b'10', ('127.0.0.1', 9999))
# print(s.recv(1024).decode('utf-8'))

# client receive
# receiver = Receive('127.0.0.1', 9999, (' ', 0), False, 10)
# receiver.Start('EP03End.mp4')


sender = Send(' ', 0, ('127.0.0.1', 9999), False, 10)
sender.Start("js.pdf")