# LFTP
计网Project-基于UDP实现可靠传输、拥塞机制、流量控制、一对多

## 使用方式注意事项：
   1. 需要更改发送的文件为自己已有的文件。
   2. 如果客户端和服务端位于同一目录下，接收方的文件会在上一目录中，若想自己调整文件路径可以在`sender.py`和`receiver.py`的`openFile`函数更改自己想要的路径。 
