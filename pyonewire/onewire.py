# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.
import _onewire
def _swig_setattr(self,class_type,name,value):
    if (name == "this"):
        if isinstance(value, class_type):
            self.__dict__[name] = value.this
            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
            del value.thisown
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    self.__dict__[name] = value

def _swig_getattr(self,class_type,name):
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0


owAcquire = _onewire.owAcquire

owRelease = _onewire.owRelease

owSpeed = _onewire.owSpeed

owFirst = _onewire.owFirst

owNext = _onewire.owNext

owSerialNum = _onewire.owSerialNum

PrintSerialNum = _onewire.PrintSerialNum

owAccess = _onewire.owAccess

owOverdriveAccess = _onewire.owOverdriveAccess

owVerify = _onewire.owVerify

owGetCurrentDir = _onewire.owGetCurrentDir

owChangeDirectory = _onewire.owChangeDirectory

owFirstFile = _onewire.owFirstFile

owNextFile = _onewire.owNextFile

owOpenFile = _onewire.owOpenFile

owMyReadFile = _onewire.owMyReadFile

myOwFirst = _onewire.myOwFirst

myOwNext = _onewire.myOwNext

owCloseFile = _onewire.owCloseFile

owCreateFile = _onewire.owCreateFile

owDeleteFile = _onewire.owDeleteFile

owWriteFile = _onewire.owWriteFile

ReadTemperature = _onewire.ReadTemperature

owGetErrorNum = _onewire.owGetErrorNum

owClearError = _onewire.owClearError

owHasErrors = _onewire.owHasErrors

owRaiseError = _onewire.owRaiseError

owPrintErrorMsgStd = _onewire.owPrintErrorMsgStd

owGetErrorMsg = _onewire.owGetErrorMsg


