class Const(object):
    class ConstError(TypeError):
        pass

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Can't change const.%s" % name)
        if not name.isupper():
            raise self.ConstCaseError('const name "%s" is not all supercase' % name)

        self.__dict__[name] = value

const = Const()
const.MSS = 50000
const.DELIMITER = '|-|:|:|-|'

const.C_SLOWSTART = 0
const.C_CAVOID = 1
const.C_FASTRECOVERY = 2

const.UPDATERWND = -1
const.JOBDONE = -2

const.HOST = "127.0.0.1"
const.PORT =  9999

# get data format: ACKnum||data||endReading
# send data format: ACK||ACKnum||rwndSize||rwnd
# server want to update rwnd format:  ' '
# receiver send rwnd back: ACK||-1||rwndSize||rwnd