# LFTP

计网Project-基于UDP实现可靠传输、拥塞机制、流量控制、一对多

## 使用方式注意事项：

   1. 客户端运行文件时需在文件后面输入 `LFTP lget myserver mylargefile` 或者 `LFTP lsend myserver mylargefile`，

      如：`python client.py LFTP lget 127.0.0.1 js.pdf`

      myserver 表示客户端的IP或URL， mylargefile表示文件名，lget则为获取，lsend则为发送
   2. 需要更改服务端host和port时，只需要在`constant.py`中更改`const.HOST`和`const.PORT`即可。
   3. 需要更改发送的文件为自己已有的文件。
   4. 如果客户端和服务端位于同一目录下，接收方的文件会在上一目录中，若想自己调整文件路径可以在`sender.py`和`receiver.py`的`openFile`函数更改自己想要的路径。 
   5. 使用的是python2，若为3请自己对部分内容略微修改。
