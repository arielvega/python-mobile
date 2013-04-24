#
#
# Copyright 2011,2013 Luis Ariel Vega Soliz and contributors.
# ariel.vega@uremix.org
#
# This file is part of python-mobile.
#
#    python-mobile is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    python-mobile is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with UADH.  If not, see <http://www.gnu.org/licenses/>.
#
#


'''
Created on 24/04/2013

@author: Luis Ariel Vega Soliz (ariel.vega@uremix.org)
@contact: Uremix Team (http://uremix.org)

'''

import hashlib
from mobile.unlocker import Unlocker

class HuaweiUnlocker(Unlocker):
    def __init__(self, device):
        self.__device = device

    def unlock(self):
        unlockcode = self.get_unlockcode() 
        return self.__device.exec_command('^CARDLOCK="'+str(unlockcode)+'"')

    def is_locked(self):
        return False

    def get_unlockcode(self):
        imei = self.__device.get_imei()
        return self.__getCode(imei, hashlib.md5("hwe620datacard").hexdigest()[8:24])

    def get_flashcode(self):
        imei = self.__device.get_imei()
        return self.__getCode(imei, hashlib.md5("e630upgrade").hexdigest()[8:24])

    def __getCode(self, imei, salt):
        digest = hashlib.md5((imei+salt).lower()).digest()
        code = 0
        for i in range(0,4):
            code += (ord(digest[i])^ord(digest[4+i])^ord(digest[8+i])^ord(digest[12+i])) << (3-i)*8
        code &= 0x1ffffff
        code |= 0x2000000
        return code