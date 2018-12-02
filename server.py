import socket
import threading
from sender import Send
from receiver import Receive
from constant import const

# test = Send('127.0.0.1', 2222, 3333, True, 5)
# test.openFile("C:/DownloadSoftware/LearningMaterials/js.pdf")
# test.Start()


def send(port, filepath, addr):
    sender = Send('127.0.0.1', port, addr, True, 10)
    sender.Start(filepath)

def receive(port, filepath, addr):
    receiver = Receive('127.0.0.1', port, addr, True, 10)
    receiver.Start(filepath)


sendPort = 1000
sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sc.bind(('127.0.0.1', 9999))
print ('Bind UDP on 9999')


while True:
    data, addr = sc.recvfrom(const.MSS)
    temp = data.split(' ')
    if temp[1] == 'lget':
        t = threading.Thread(target= send, args= (sendPort, temp[3], addr))
        t.start()
    else:
        t = threading.Thread(target= receive, args= (sendPort, temp[3], addr))
        t.start()
    sendPort += 1000
    
