import socket
import threading
import time
import numpy as np
from constant import const
from multiprocessing import Process

class Send(object):

    def __init__(self, host, port, addr, server, windowSize):
        self.sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server
        self.windowSize = windowSize
        self.fileOpen = False
        self.lock = threading.Lock()
        self.sendAddr = addr
        if server:
            self.sc.bind((host, port))
        
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

    def Start(self, filepath):
        self.openFile(filepath)
        if not self.fileOpen:
            print("You haven't set the path of file yet.")
            return
        # confirm the size of the rwnd
        if self.server:
            message = "server prepares to send data"
        else:
            message = "LFTP lsend 127.0.0.1 " + filepath
        self.sc.sendto(message, self.sendAddr)
        rwndData, self.sendAddr = self.sc.recvfrom(const.MSS)
        self.rwnd = int(rwndData.decode('utf-8'))

        self.InitialAndStartThreads()
    
    def InitialAndStartThreads(self):
        # initial
        # print("rwndData: {} sendAddr: {} ".format(self.rwndData, self.sendAddr))
        self.sendQueue = []
        self.queueBase = 0
        self.queueNextNum = 0
        self.endReading = 0

        self.cwnd = 1.0
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
            #set lock
            self.lock.acquire()
            sendSize = np.min([self.rwnd, self.cwnd])
            send = self.send
            self.lock.release()
            # print("before send: rwnd: {} cwnd: {}".format(self.rwnd, self.cwnd))
            if sendSize == 0:
                self.sc.sendto(' ', self.sendAddr)
                # print("\nrwnd is 0, send a small message to get new rwnd")
                time.sleep(0.01)
            elif send:
                for size in range(int(sendSize)):
                    # judge the sender can send or not. satisfy the buffers of itself and receiver 
                    # flow control
                    if self.queueNextNum < self.queueBase + self.windowSize and self.queueNextNum - self.queueBase < self.rwnd:
                        data = self.file.read(const.MSS)
                        if len(data) < const.MSS:
                            print("end reading")
                            self.endReading = const.JOBDONE
                        # send the queueNum + data
                        data = str(self.queueNextNum) + const.DELIMITER + data + const.DELIMITER + str(self.endReading)
                        # print("\nsend ACK: {} ".format(self.queueNextNum))
                        # set lock
                        self.lock.acquire()
                        self.sc.sendto(data, self.sendAddr)
                        self.sendQueue.append(data)
                        if self.queueNextNum == self.queueBase:
                            self.timerStart(self.timecancel)
                        self.queueNextNum += 1
                        self.lock.release()
                        if self.endReading == const.JOBDONE:
                            break
                # set lock
                self.lock.acquire()
                self.send = False
                self.lock.release()
                if self.endReading == const.JOBDONE:
                    break
               
        print('All data has been sent. Close file.')
        self.file.close()

    def Resend(self, fastRecover):
        if not fastRecover:
            print("time out")
        print("resend")
        self.timerStart(self.timecancel)
        # set lock
        self.lock.acquire()
        # print(len(self.sendQueue))
        for data in self.sendQueue:
            temp = data.split(const.DELIMITER)
            print("resend ACK: {} ".format(temp[0]))
            self.sc.sendto(data, self.sendAddr)
        # change congestion state
        if not fastRecover:
            self.congestionState = const.C_SLOWSTART
            if self.cwnd < 2:
                self.ssthresh = 1.0
            else:
                self.ssthresh = self.cwnd / 2
            self.cwnd = 1.0
            self.dupACKcount = 0
            print("change state to slow fast")
            print("cwnd: {} ssthresh: {}".format(self.cwnd, self.ssthresh))
        self.lock.release()
    
    def getNewACK(self):
        # set lock
        print("get newACK")
        # print(len(self.sendQueue))
        self.lock.acquire()
        del self.sendQueue[0]
        self.queueBase += 1
        self.lock.release()
        # set timer state
        self.dupACKcount = 0
        if self.queueNextNum == self.queueBase:
            self.timer.cancel()
            self.timecancel = True
        else:
            self.timerStart(self.timecancel)
        
    def getDupACK(self):
        print("get dupACK: {}".format(self.dupACKcount + 1))
        self.dupACKcount += 1
        if self.dupACKcount == 3:
            # set lock
            self.lock.acquire()
            if self.cwnd < 2:
                self.ssthresh = 1.0
                self.cwnd = 1.0
            else:
                self.ssthresh = self.cwnd / 2
                self.cwnd = self.cwnd / 2 + 3
            self.lock.release()
            self.Resend(True)
            self.congestionState = const.C_FASTRECOVERY
            print("change state to fast recovery")
            print("cwnd: {} ssthresh: {}".format(self.cwnd, self.ssthresh))

    def receiveData(self):
        while True:
            # get response data
            # if self.server:
            self.recvData, self.sendAddr = self.sc.recvfrom(const.MSS)
            # else:
            #     self.recvData = self.sc.recv(const.MSS)
            temp = self.recvData.split(const.DELIMITER)
            # print('receive data: {}'.format(self.recvData))
            ACKnum = int(temp[1])
            # done
            if ACKnum == const.JOBDONE:
                print('All data has been received. Close Connection.')
                self.sc.close()
                self.timer.cancel()
                break

            # update rwnd
            self.rwnd = int(temp[3])
            # print("get the size of rwnd is : {}".format(self.rwnd))
            if ACKnum == const.UPDATERWND:
                # print("update ACKnum")
                # set lock
                self.lock.acquire()
                self.send = True
                self.lock.release()
                # print("rwnd: {}, send: {}".format(self.rwnd, self.send))
                continue

            # congestion control   
            # slow-fast
            if self.congestionState == const.C_SLOWSTART:
                print("now congestion state: slow fast")
                if ACKnum == self.queueBase:
                    self.getNewACK()
                    #set lock
                    self.lock.acquire()
                    self.send = True
                    # update cwnd
                    if self.cwnd < self.ssthresh:
                        if self.cwnd + 1 <= self.ssthresh:
                            self.cwnd += 1
                        else:
                            self.cwnd = self.ssthresh
                    if self.cwnd >= self.ssthresh:
                        print("change state to congestion avoid")
                        self.congestionState = const.C_CAVOID
                    self.lock.release()
                    print("cwnd: {} ssthresh: {}".format(self.cwnd, self.ssthresh))
                else:
                    self.getDupACK()

            # congestion-avoid
            elif self.congestionState == const.C_CAVOID:
                print("now congestion state: congestion avoid")
                if ACKnum == self.queueBase:
                    self.getNewACK()
                    #set lock
                    self.lock.acquire()
                    self.send = True
                    # update cwnd
                    self.cwnd += 1.0 / int(self.cwnd)
                    self.lock.release()
                else:
                    self.getDupACK()
                print("cwnd: {} ssthresh: {}".format(self.cwnd, self.ssthresh))
                

            # fast-recovery
            else:
                print("now congestion state: fast recovery")
                if ACKnum == self.queueBase:
                    self.getNewACK()
                    # set lock
                    self.lock.acquire()
                    self.cwnd = self.ssthresh
                    self.lock.release()
                    self.congestionState = const.C_CAVOID
                    print("change state to congestion avoid")
                else:
                    # set lock
                    self.lock.acquire()
                    self.cwnd += 1
                    self.send = True
                    self.lock.release()
                print("cwnd: {}, ssthresh: {}".format(self.cwnd, self.ssthresh))
