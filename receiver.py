import socket
import threading
import time
import binascii 
import numpy as np
from constant import const

class Receive(object):

    def __init__(self, host, port, addr, server, receiveBuffer):
        self.sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server
        self.receiveBuffer = receiveBuffer
        self.rwnd = self.receiveBuffer
        self.sendAddr = addr
        self.lock = threading.Lock()
        self.fileOpen = False
        if server:
            self.sc.bind((host, port))
        else:
            self.sendAddr = (host, port)
    
    def openFile(self, filepath):
        try:
            self.file = open(filepath.decode('utf-8'), 'wb')
            self.fileOpen = True
        except:
            print("The file doesn't exist.")

    def closeFile(self):
        if (self.fileOpen):
            self.file.close()
        else:
            print("You didn't open a file before.")
    
    def Start(self,filepath):
        self.openFile("../" + filepath)
        if not self.fileOpen:
            print("You haven't set the path of file yet.")
            return
        if self.server:
            self.sc.sendto(b'%d' % self.receiveBuffer, self.sendAddr)
            print('server prepares to receive data')
        else:
            message = "LFTP lget " + str(self.sendAddr[0]) + " " + filepath
            self.sc.sendto(message, self.sendAddr)
            data, self.sendAddr = self.sc.recvfrom(const.MSS)
            if cmp(data.decode('utf-8'), 'server prepares to send data') == 0:
                self.sc.sendto(b'%d' % self.receiveBuffer, self.sendAddr)
                print('client prepares to receive data')
        
        self.InitialAndStartThreads()
        
    def InitialAndStartThreads(self):
        # initial
        self.receiverQueue = []
        self.lastRcvd = 0
        self.lastRead = 0
        self.ACK = -1
        self.done = False

        # start threads
        self.receiveThread = threading.Thread(target=self.receiveData, name='ReceiveThread')
        self.storeThread = threading.Thread(target=self.storeData, name='storeThread')
        self.receiveThread.start()
        self.storeThread.start()
        self.receiveThread.join()
        self.storeThread.join()

    def receiveData(self):
        while True:
            # if have buffer to get data
            #set lock
            self.lock.acquire()
            rwnd = self.receiveBuffer - (self.lastRcvd - self.lastRead)
            self.lock.release()
            if rwnd == 0:
                continue
            
            # get data
            self.recvData, self.sendAddr = self.sc.recvfrom(2 * const.MSS)
            
            # drop packet test
            # rand = np.random.random()
            # if rand > 0.9:
            #     print("drop the packet test, the rand is {}".format(rand))
            #     continue

            temp = self.recvData.split(const.DELIMITER)
            if temp[0] == ' ':
                #set lock
                self.lock.acquire()
                resData = "ACK" + const.DELIMITER + str(const.UPDATERWND) + const.DELIMITER + "rwndSize" + const.DELIMITER + str(self.rwnd)
                self.lock.release()
                self.sc.sendto(resData, self.sendAddr)
                print("update rwnd for server")
                print(resData)
                continue
            sendACK = (int(temp[0]))
            if self.ACK + 1 == sendACK:
                #set lock
                print('get ACK: {}'.format(sendACK))
                self.lock.acquire()
                self.receiverQueue.append(temp[1])
                self.lock.release()
                self.lastRcvd += 1
                self.ACK += 1
                if int(temp[2]) == const.JOBDONE:
                    resData = "ACK" + const.DELIMITER + str(const.JOBDONE)
                    self.sc.sendto(resData, self.sendAddr)
                    print("done ACK: {}".format(temp[0]))
                    self.done = True
                    break
            # response
            #set lock
            self.lock.acquire()
            rwnd = self.receiveBuffer - (self.lastRcvd - self.lastRead)
            # print("lastRcvd: {}, lastRead: {}".format(self.lastRcvd, self.lastRead))
            resData = "ACK" + const.DELIMITER + str(sendACK) + const.DELIMITER + "rwndSize" + const.DELIMITER + str(rwnd)
            self.lock.release()
            self.sc.sendto(resData, self.sendAddr)
            print("response: {}".format(resData))


    def storeData(self):
        try:
            while True:
                time.sleep(0.01)
                #set lock
                self.lock.acquire()
                while len(self.receiverQueue) > 0:
                    self.file.write(self.receiverQueue[0])
                    self.lastRead += 1
                    del self.receiverQueue[0]
                    # print("receiverQueueSize: {}, lastRead: {}".format(len(self.receiverQueue), self.lastRead))
                self.lock.release()
                if self.done:
                    print("All data has benn received. Close Connection.")
                    break
        finally:
            self.file.close()
            self.sc.close()