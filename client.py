#!/usr/bin/python
# coding:UTF-8
import socket
import threading
import time
import binascii 
import numpy as np
from constant import const

class Receive(object):

    def __init__(self, host, port, server, receiveBuffer):
        self.sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server
        self.receiveBuffer = receiveBuffer
        self.rwnd = self.receiveBuffer
        self.lock = threading.Lock()
        if server:
            self.sc.bind((host, port))
            print ('Bind UDP on %d' % port)
        else:
            self.sendAddr = (host, port)
        self.fileOpen = False
    
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
    
    def Start(self):
        if self.server:
            data, addr = self.sc.recvfrom(const.MMS)
            if cmp(data.decode('utf-8'), 'client prepares to send data') == 0:
                self.sc.sendto(b'%d' % self.receiveBuffer, addr)
                print('server prepares to receive data')
            # print(rwndData.decode('utf-8'))
            # print(addr)
        else:
            self.sc.sendto(b'%d' % self.receiveBuffer, self.sendAddr)
            print('client prepares to receive data')

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
            self.recvData, self.sendAddr = self.sc.recvfrom(2 * const.MMS)
            
            # #drop packet test
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
            print("lastRcvd: {}, lastRead: {}".format(self.lastRcvd, self.lastRead))
            resData = "ACK" + const.DELIMITER + str(sendACK) + const.DELIMITER + "rwndSize" + const.DELIMITER + str(rwnd)
            self.lock.release()
            self.sc.sendto(resData, self.sendAddr)
            print("response: {}".format(resData))


    def storeData(self):
        try:
            while True:
                time.sleep(0.1)
                #set lock
                self.lock.acquire()
                while len(self.receiverQueue) > 0:
                    self.file.write(self.receiverQueue[0])
                    self.lastRead += 1
                    del self.receiverQueue[0]
                    print("receiverQueueSize: {}, lastRead: {}".format(len(self.receiverQueue), self.lastRead))
                self.lock.release()
                if self.done:
                    print("All data has benn received. Close Connection.")
                    break
        finally:
            self.file.close()
            self.sc.close()


# get data format: ACKnum||data||endReading
# send data format: ACK||ACKnum||rwndSize||rwnd
# server want to update rwnd format:  ' '
# receiver send rwnd back: ACK||-1||rwndSize||rwnd

# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.sendto(b'10', ('127.0.0.1', 9999))
# print(s.recv(1024).decode('utf-8'))

test = Receive('47.107.126.23', 2222, False, 5)
test.openFile("../js.pdf")
test.Start()