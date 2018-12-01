import socket
import threading
import time
import numpy as np
from constant import const

class Send(object):

    def __init__(self, host, port, server, windowSize):
        self.sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server
        self.windowSize = windowSize
        self.fileOpen = False
        self.lock = threading.Lock()
        if (server):
            self.sc.bind((host, port))
            print ('Bind UDP on %d' % port)
        else:
            self.sendAddr = (host, port)
        
    
    def openFile(self, filepath):
        try:
            self.file = open(filepath.decode('utf-8'), 'rb')
            self.fileOpen = True
        except:
            print("The file doesn't exist.")

    def closeFile(self):
        if (self.fileOpen):
            self.file.close()
        else:
            print("You didn't open a file before.")

    def Start(self):
        if not self.fileOpen:
            print("You haven't set the path of file yet.")
            return
        # confirm the size of the rwnd
        if self.server:
            rwndData, self.sendAddr = self.sc.recvfrom(const.MMS)
            # self.sendAddr = addr
            self.rwnd = int(rwndData.decode('utf-8'))
        else:
            self.sc.sendto(b'client prepares to send data', self.sendAddr)
            rwndData = self.sc.recv(const.MMS)
            self.rwnd = int(rwndData.decode('utf-8'))
        # initial
        print("rwndData: {} sendAddr: {} ".format(rwndData, self.sendAddr))
        self.sendQueue = []
        self.queueBase = 0
        self.queueNextNum = 0
        self.endReading = 0

        self.cwnd = 5.0
        self.ssthresh = 50.0
        self.send = True
        self.timecancel = True
        self.dupACKcount = 0
        self.congestionState = const.C_SLOWSTART

        # start threads
        self.sendThread = threading.Thread(target=self.sendData, name='SendThread')
        self.receiveThread = threading.Thread(target=self.receiveData, name='ReceiveThread')
        self.sendThread.start()
        self.receiveThread.start()
        self.sendThread.join()
        self.receiveThread.join()

    def timerStart(self, cancel):
        if not cancel:
            self.timer.cancel()
        self.timer = threading.Timer(2.0, self.Resend, [False])
        self.timer.start()
        self.timecancel = False

    def sendData(self):
        while True:
            # get the reveiver the dataSize can get
            sendSize = np.min([self.rwnd, self.cwnd])
            # print("before send: rwnd: {} cwnd: {}".format(self.rwnd, self.cwnd))
            # print("send is {}".format(self.send))
            if sendSize == 0:
                self.sc.sendto(' ', self.sendAddr)
                print("rwnd is 0, send a small MMS to get new rwnd")
            elif self.send:
                for size in range(int(sendSize)):
                    # judge the sender can send or not. satisfy the buffers of itself and receiver 
                    # flow control
                    if self.queueNextNum < self.queueBase + self.windowSize and self.queueNextNum - self.queueBase < self.rwnd:
                        data = self.file.read(const.MMS)
                        # print("read data {}: {} ,data length: {}".format(self.queueNextNum, data, len(data)))
                        if len(data) < const.MMS:
                            print("end reading")
                            self.endReading = const.JOBDONE
                        # send the queueNum + data
                        data = str(self.queueNextNum) + const.DELIMITER + data + const.DELIMITER + str(self.endReading)
                        self.sc.sendto(data, self.sendAddr)
                        print("send queueNum: {} ".format(self.queueNextNum))
                        # set lock
                        # self.lock.acquire()
                        self.sendQueue.append(data)
                        if self.queueNextNum == self.queueBase:
                            self.timerStart(self.timecancel)
                        self.queueNextNum += 1
                        # self.lock.release()
                self.send = False
                if self.endReading == const.JOBDONE:
                    break
               
        print('All data has been sent. Close file.')
        self.file.close()

    def Resend(self, fastRecover):
        print("resend")
        self.timerStart(self.timecancel)
        # set lock
        # self.lock.acquire()
        print(len(self.sendQueue))
        for data in self.sendQueue:
            temp = data.split(const.DELIMITER)
            print("send ACK:{} endreading:{}".format(temp[0], temp[2]))
            self.sc.sendto(data, self.sendAddr)
        # self.lock.release()
        # change congestion state
        if not fastRecover:
            self.congestionState = const.C_SLOWSTART
            self.ssthresh = self.cwnd / 2
            self.cwnd = 5.0
            self.dupACKcount = 0
        
    
    def getNewACK(self):
        # set lock
        # self.lock.acquire()
        print("get newACK")
        del self.sendQueue[0]
        self.queueBase += 1
        # self.lock.release()
        self.dupACKcount = 0
        # set timer state
        self.send = True
        if self.queueNextNum == self.queueBase:
            self.timer.cancel()
            self.timecancel = True
        else:
            self.timerStart(self.timecancel)
        
        

    def getDupACK(self):
        print("get dupACK")
        self.dupACKcount += 1
        if self.dupACKcount == 3:
            self.ssthresh = self.cwnd / 2
            self.cwnd = self.cwnd / 2 + 3
            self.Resend(True)
            self.congestionState = const.C_FASTRECOVERY

    def receiveData(self):
        while True:
            # get response data
            # if self.server:
            self.recvData, self.sendAddr = self.sc.recvfrom(const.MMS)
            # else:
            #     self.recvData = self.sc.recv(const.MMS)
            temp = self.recvData.split(const.DELIMITER)
            print('receive data: {}'.format(temp))
            ACKnum = int(temp[1])
            # done
            if ACKnum == const.JOBDONE:
                print('All data has been received. Close Connection.')
                self.sc.close()
                self.timer.cancel()
                break

            # update rwnd
            self.rwnd = int(temp[3])
            print(ACKnum)
            print(ACKnum == const.UPDATERWND)
            if ACKnum == const.UPDATERWND:
                print("update ACKnum\n")
                self.send = True
                print("rwnd: {}, send: {}".format(self.rwnd, self.send))
                continue

            # congestion control   
            # slow-fast
            if self.congestionState == const.C_SLOWSTART:
                if ACKnum == self.queueBase:
                    self.getNewACK()
                    # update cwnd
                    if self.cwnd + 1 < self.ssthresh:
                        self.cwnd += 1
                    else:
                        self.cwnd = self.ssthresh
                        self.congestionState = const.C_CAVOID
                    print("update cwnd: {}".format(self.cwnd))
                else:
                    self.getDupACK()

            # congestion-avoid
            elif self.congestionState == const.C_CAVOID:
                if ACKnum == self.queueBase:
                    self.getNewACK()
                    # update cwnd
                    self.cwnd += 1.0 / int(self.cwnd)
                else:
                    self.getDupACK()

            # fast-recovery
            else:
                if ACKnum == self.queueBase:
                    self.cwnd = self.ssthresh
                    self.dupACKcount = 0
                    self.congestionState = const.C_CAVOID
                else:
                    self.cwnd += 1
                    self.send = True
            print("cwnd: {}, ssthresh: {}".format(self.cwnd, self.ssthresh))

test = Send('127.0.0.1', 5555, True, 10)
test.openFile("C:/DownloadSoftware/LearningMaterials/EP03End.mp4")
test.Start()