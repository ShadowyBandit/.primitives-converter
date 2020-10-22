''' ShadowHunterRUS 2015-2016 '''



#####################################################################
# imports

from ctypes import c_long
from mathutils import Vector, Matrix
from ..common.XmlUnpacker import XmlUnpacker



#####################################################################
# globals

g_XmlUnpacker = XmlUnpacker()



#####################################################################
# functions

def shr_AsVector(vector_str):
    return Vector(tuple(map(float, vector_str.strip().split())))



def shr_AsMatrix4x4T(vector_str):
    vector_16 = shr_AsVector(vector_str)
    return Matrix(
        (vector_16[:4], vector_16[4:8], vector_16[8:12], vector_16[12:16])).transposed()



def shr_AsBool(bool_str):
    if 'true' in bool_str.lower():
        return True
    return False



def shr_AsInt(int_str):
    if int_str is None:
        shr_PrintError('shr_AsInt: int_str is None')
    int_str = int_str.strip()
    if int_str.isdigit():
        return int(int_str)
    return 0



def shr_AsFloat(float_str):
    return float(float_str)



def shr_AsNormPath(path_str):
    return '/'.join(path_str.strip().split('\\'))



def shr_Log(log_str):
    if True:
        print(log_str)
    else:
        with open('log.txt', 'a') as f:
            f.write(log_str)



def shr_PrintInfo(info_str):
    shr_Log('Info: %s' % info_str)



def shr_PrintWarn(warn_str):
    shr_Log('Warn: %s' % warn_str)



def shr_PrintError(err_str):
    shr_Log('Error: %s' % err_str)



def shr_PrintSplitter():
    shr_Log('='*12)



def shr_UnpackNormal(packed):
    pkz = (c_long(packed).value>>22)&0x3FF
    pky = (c_long(packed).value>>11)&0x7FF
    pkx = (c_long(packed).value)&0x7FF
    if pkx > 0x3ff:
	    x = -float((pkx&0x3ff^0x3ff)+1)/0x3ff
    else:
	    x = float(pkx)/0x3ff
    if pky > 0x3ff:
	    y = -float((pky&0x3ff^0x3ff)+1)/0x3ff
    else:
	    y = float(pky)/0x3ff
    if pkz > 0x1ff:
	    z = -float((pkz&0x1ff^0x1ff)+1)/0x1ff
    else:
	    z = float(pkz)/0x1ff
    return Vector((x, z, y))



def shr_UnpackNormal_tag3(packed):
    pkz = (packed>>16)&0xFF^0xFF
    pky = (packed>>8)&0xFF^0xFF
    pkx = packed&0xFF^0xFF
    if pkx > 0x7f:
        x = -float(pkx&0x7f)/0x7f
    else:
        x = float(pkx^0x7f)/0x7f
    if pky > 0x7f:
        y = -float(pky&0x7f)/0x7f
    else:
        y = float(pky^0x7f)/0x7f
    if pkz>0x7f:
        z = -float(pkz&0x7f)/0x7f
    else:
        z = float(pkz^0x7f)/0x7f
    return Vector((x, z, y))
