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
const.MMS = 5000
const.DELIMITER = '|-|:|:|-|'

const.C_SLOWSTART = 0
const.C_CAVOID = 1
const.C_FASTRECOVERY = 2

const.UPDATERWND = -1
const.JOBDONE = -2