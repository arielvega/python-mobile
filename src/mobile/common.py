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
Created on 04/03/2012

@author: Luis Ariel Vega Soliz (ariel.vega@uremix.org)
@contact: Uremix Team (http://uremix.org)

'''

import re, os, datetime
import threading
import time
from mobile import pdu

__all__ = ['PhoneBook', 'PhoneBookEntry', 'SMS', 'CommonThread']

EOL = '\r\n'
EOF = chr(26)
RWSTORAGE = ['SM', 'ME', 'MT']
STATUSSTRTOCODE = {'REC UNREAD':0, 'REC READ':1, 'STO UNSENT':2, 'STO SENT':3, 'ALL':4}
STATUSCODETOSTR = {0:'REC UNREAD', 1:'REC READ', 2:'STO UNSENT', 3:'STO SENT', 4:'ALL'}
KNOWNSERIALPORTS = ['ttyS', 'ircomm', 'ttyUB', 'ttyUSB', 'rfcomm', 'ttyACM', 'COM']
''' 
# Serial device to which the mobile device may be connected:
/dev/ttyS*    for serial port, 
/dev/ircomm*  for IrDA,
/dev/ttyUB*   for Bluetooth (Bluez with rfcomm running),
/dev/ttyUSB*  for USB,
/dev/rfcomm*  Bluetooth serial port
/dev/ttyACM*  for USB ACM 

from: http://www.lugmen.org.ar/pipermail/lug-list/2005-April/035245.html
'''

'''
AT^SYSCFG=mode,order,band,roaming,domain - System Config
    mode:
        2      Automatic search
        13     2G only
        14     3G only
        16     No change
        
    order:
        0    Automatic search
        1    2G first, then 3G
        2    3G first, then 2G
        3    No change
        
    band:
        80            GSM DCS systems
        100           Extended GSM 900
        200           Primary GSM 900
        200000        GSM PCS
        400000        WCDMA IMT 2000
        3FFFFFFF      Any band
        40000000      No change
    
    roaming:
        0    Not supported
        1    Roaming is supported
        2    No change
    
    domain:
        0    CS_ONLY
        1    PS_ONLY
        2    CS_PS
        3    ANY
        4    No change

from: https://wiki.archlinux.org/index.php/Huawei_E1550_3G_modem
'''

ascii = re.compile('[a-zA-Z \r\n\t&\\\+\-\_\:\;\=\.\*\%!|@?\<\>\(\)0-9/\'\"\[\]\{\}\$]+',re.IGNORECASE)

SMS_ASCII_LENGHT = 140
SMS_NON_ASCII_LENGHT = 70

def get_sms_lenght(text):
    if ascii.match(text):
        return SMS_ASCII_LENGHT
    return SMS_NON_ASCII_LENGHT

def split_sms_text(text):
    lenght = get_sms_lenght(text)
    l = []
    while len(text)>0:
        l.append(text[:lenght])
        text = text[lenght:]
    return l

def exist_port(port):
    port = get_os_port(port)
    if os.name == 'nt': #sys.platform == 'win32':
        return True
    else:
        return os.path.exists(port)

def get_os_port(port):
    oldport = False
    if type(port) == type(''):
        port = port.strip()
        if not port.isdigit():
            if port.startswith('/dev/'):
                port = port[5:]
            if port.upper().startswith('COM'):
                port = port[3:]
            else:
                for tp in KNOWNSERIALPORTS:
                    if port.startswith(tp):
                        oldport = port
                        port = port[len(tp):]
                        break
    if os.name == 'nt': #sys.platform == 'win32':
        return 'COM' + port
    elif os.name == 'posix':
        if not oldport:
            return '/dev/ttyUSB' + str(port)
        else:
            return '/dev/' + oldport
    else:
        raise Exception("Sorry: no implementation for your platform ('%s') available" % os.name)

def smspdu2sms(smspdu, pos, status, device):
    print smspdu
    smscnumberlen = pdu.hex2int(smspdu[ : 2])
    SMSC = smspdu[2: 2+(smscnumberlen*2)]
    smscnumbertype = SMSC[:2]
    smsc = pdu.semioctet2string(SMSC[2:])
    if (smscnumbertype == '91' and not smsc.startswith('+')):
        smsc = '+'+smsc
    if (smsc.endswith('F')):
        smsc = smsc[:-1]
    TPDU = smspdu[2+(smscnumberlen*2): ]
    fosmsdeliver = TPDU[ :2]
    senderlen = pdu.hex2int(TPDU[2 : 2 +2])
    if((senderlen % 2)<>0):
        senderlen = senderlen + 1
    sendernumbertype = TPDU[2+2 : 2+2 +2]
    sender = pdu.semioctet2string(TPDU[2+2+2 : 2+2+2 +senderlen])
    if (sendernumbertype == '91' and not sender.startswith('+')):
        sender = '+'+sender
    if (sender.endswith('F')):
        sender = sender[:-1]
    protocolID = TPDU[2+2+2+senderlen : 2+2+2+senderlen +2]
    encoding = TPDU[2+2+2+senderlen+2 : 2+2+2+senderlen+2 +2]
    date = pdu.pdudate2date(TPDU[2+2+2+senderlen+2+2 : 2+2+2+senderlen+2+2 +14])
    smslen = pdu.hex2int(TPDU[2+2+2+senderlen+2+2+14 : 2+2+2+senderlen+2+2+14 +2])
    smstext = pdu.decode(TPDU[2+2+2+senderlen+2+2+14+2 :])
    return SMS(smstext, sender, date, pos, status, device)

def pduread2sms((txt, device), pos):
    txt = txt[6:]
    txt = txt.strip().split('\n')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) <> 2):
        return
    try:
        smspdu = txt[-1]
        txt = txt[0].strip().split(',')
        while(txt.count('')>0):
            txt.remove('')
        status = STATUSCODETOSTR[int(txt[0])]
        return smspdu2sms(smspdu, pos, status, device)
    except Exception, ex:
        print ex
        return

def pdulist2sms((txt, device)):
    txt = txt[6:]
    txt = txt.strip().split('\n')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) <> 2):
        return
    try:
        smspdu = txt[-1]
        txt = txt[0].strip().split(',')
        while(txt.count('')>0):
            txt.remove('')
        pos = txt[0]
        status = STATUSCODETOSTR[int(txt[1])]
        return smspdu2sms(smspdu, pos, status, device)
    except Exception, ex:
        print ex
        return

def parse_CMGR_txt_to_sms((txt, device), pos):
    txt = txt[6:]
    txt = txt.strip().split('\n')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) < 2):
        return
    try:
        if(len(txt) == 2):
            message = txt[-1]
        else:
            message = '\n'.join(txt[1:])
        txt = txt[0].strip().split(',')
        while(txt.count('')>0):
            txt.remove('')
        memory = txt[0].replace('"','')
        phone = txt[1].replace('"','')
        if(len(txt)>1):
            date = (txt[-2] +', '+ txt[-1]).replace('"','')
        else:
            date=''
        return SMS(message, phone, date, pos, memory, device)
    except Exception, ex:
        print ex
        return


def parse_txt_to_sms((txt, device)):
    txt = txt.strip().split('\n')
    #if (txt.count('ERROR')>0):
    #    return
    #while(txt.count('OK')>0):
    #    txt.remove('OK')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) < 2):
        return
    try:
        if(len(txt) == 2):
            message = txt[-1]
        else:
            message = '\n'.join(txt[1:])
        txt = txt[0].strip().split(',')
        while(txt.count('')>0):
            txt.remove('')
        pos = txt[0].replace('"','')
        memory = txt[1].replace('"','')
        phone = txt[2].replace('"','')
        if(len(txt)>3):
            date = (txt[3] +', '+ txt[4]).replace('"','')
        else:
            date=''
        return SMS(message, phone, date, pos, memory, device)
    except Exception, ex:
        print ex
        return


class SMS:
    ''' Represents a SMS, it can be sent or deleted '''
    def __init__(self, message, phone, date = datetime.date.today().strftime('%y/%m/%d,%T'), pos = -1, memory = 'VOLATILE', device = None):
        self.__phone_number = phone
        self.__message = message
        self.__date = date
        self.__position = int(pos)
        self.__memory = memory
        self.__device = device

    def send(self):
        if (self.__device == None) or (self.get_memory() == 'REC READ'):
            print 'no se puede enviar el mensaje'
            print self
            return False
        return self.__device.send_sms(self)

    def delete(self):
        if self.__device == None:
            return
        return self.__device.delete_sms(self)

    def get_phone_number(self):
        return self.__phone_number

    def get_message(self):
        return self.__message

    def get_date(self):
        return self.__date

    def get_position(self):
        return self.__position

    def get_memory(self):
        return self.__memory

    def set_phone_number(self, number):
        self.__phone_number = number

    def set_message(self, message):
        self.__message = message

    def set_date(self, date):
        self.__date = date

    def set_position(self, position):
        self.__position = position

    def set_memory(self, memory):
        self.__memory = memory

    def __str__(self):
        res = str(self.__phone_number) +'> '+ self.__message# + 'Date: '+ self.__date
        return res[:15].replace('\n','')+'...'

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        if other == None:
            return False
        return self.get_date() > other.get_date()

    def __le__(self, other):
        if other == None:
            return False
        return self.get_date() >= other.get_date()

    def __eq__(self, other):
        if other == None:
            return False
        return self.get_date() == other.get_date()

    def __ne__(self, other):
        if other == None:
            return True
        return self.get_date() <> other.get_date()

    def __gt__(self, other):
        if other == None:
            return False
        return self.get_date() < other.get_date()

    def __ge__(self, other):
        if other == None:
            return False
        return self.get_date() <= other.get_date()

    def __cmp__(self, other):
        if other == None:
            return False
        return cmp(self.get_date(), other.get_date())

    def __hash(self):
        return hash(self.get_date())


def parse_txt_to_phonebook((txt, device)):
    txt = txt.strip().split('\r\n')
    if (txt.count('ERROR')>0):
        return PhoneBook('VOLATILE', 10, device)
    while(txt.count('OK')>0):
        txt.remove('OK')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) == 0):
        return PhoneBook('VOLATILE', 10, device)
    try:
        txt = txt[0].strip().split(',')
        while(txt.count('')>0):
            txt.remove('')
        location = txt[0].replace('"','')
        capacity = txt[2].replace('"','')
        return PhoneBook(location, capacity, device)
    except:
        return PhoneBook('VOLATILE', 10, device)



class PhoneBook:
    ''' Represents a phonebook '''
    def __init__(self, location, capacity, device):
        self.__location = location
        self.__capacity = int(capacity)
        self.__device = device
        self.__entries = []
        self.__used = 0

    def get_location(self):
        return self.__location

    def get_used(self):
        return self.__used

    def get_capacity(self):
        return self.__capacity

    def add_entries(self, entry):
        if len(self.__entries) == 0:
            self.load()
        if isinstance(entry, list):
            for i in entry:
                self.add_entry(i)

    def add_entry(self, entry):
        if len(self.__entries) == 0:
            self.load()
        if isinstance(entry, PhoneBookEntry):
            if self.__entries[entry.get_position() - 1] <> None :
                if self.__entries[entry.get_position() - 1] <> entry :
                    entry.set_position(self.get_free_position())
                else:
                    return
            if self.__entries.count(entry)>0:
                return
            self.__entries[entry.get_position() - 1] = entry
            self.__used = self.__used + 1

    def get_free_position(self):
        i = 0
        while i < self.__capacity:
            if self.__entries[i] == None:
                return i + 1
            i = i + 1
        return None

    def create_entry(self, name, phone):
        return PhoneBookEntry(name, phone, self.get_free_position(), phonebook = self)

    def delete_entry(self, entry):
        self.__device._delete_phonebook_entry(self.__location, entry)
        self.__used = self.__used - 1

    def save_entry(self, entry):
        self.__device._save_phonebook_entry(self.__location, entry)

    def load(self):
        if len(self.__entries) == 0:
            i = 0
            while i < self.__capacity:
                self.__entries.append(None)
                i = i + 1
        entries = self.__device._get_phonebook_entries(self.__location)
        for entry in entries:
            if entry <> None:
                self.__entries[entry.get_position() - 1] = entry
                self.__used = self.__used + 1

    def __str__(self):
        return 'Storage: ' + self.__location + '\nMax: ' + str(self.__capacity) + '\nUsed: ' + str(self.get_used()) + '\nEntries:\n' + '\n'.join([str(i) for i in self.__entries])

    def __repr__(self):
        return str(self)

    def __iter__(self):
        for e in self.__entries:
            if e <> None:
                yield e

def parse_txt_to_phonebook_entry((txt, memory)):
    txt = txt.strip().split('\r\n')
    if (txt.count('ERROR')>0):
        return
    while(txt.count('OK')>0):
        txt.remove('OK')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) == 0):
        return
    try:
        txt = txt[0].strip().split(',')
        while(txt.count('')>0):
            txt.remove('')
        pos = txt[0].replace('"','')
        phone = txt[1].replace('"','')
        type = txt[2].replace('"','')
        name = txt[3].replace('"','')
        return PhoneBookEntry(name, phone, pos, type, memory)
    except:
        return


class PhoneBookEntry:
    ''' It represents a entry on the phonebook '''
    def __init__(self, name, phone, pos = -1, atype = 129, phonebook = None):
        self.__name = name
        self.__phone_number = phone
        self.__position = int(pos)
        self.__type = atype
        self.__phonebook = phonebook

    def get_name(self):
        return self.__name

    def get_phone_number(self):
        return self.__phone_number

    def get_position(self):
        return self.__position

    def get_type(self):
        return self.__type

    def get_phonebook(self):
        return self.__phonebook

    def set_name(self, name):
        self.__name = name

    def set_phone_number(self, number):
        self.__phone_number = number

    def set_position(self, position):
        self.__position = position

    def set_type(self, type):
        self.__type = type

    def set_phonebook(self, phonebook):
        self.__phonebook = phonebook

    def delete(self):
        self.__phonebook.delete_entry(self)

    def save(self):
        self.__phonebook.save_entry(self)

    def __str__(self):
        return self.__name + ': ' + str(self.__phone_number)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        try:
            return self.__name == other.get_name() and self.__phone_number == other.get_phone_number() and self.__type == other.get_type()
        except:
            return False

    def __neq__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if other == None:
            return False
        return self.get_name() < other.get_name()

    def __le__(self, other):
        if other == None:
            return False
        return self.get_name() <= other.get_name()

    def __gt__(self, other):
        if other == None:
            return False
        return self.get_name() > other.get_name()

    def __ge__(self, other):
        if other == None:
            return False
        return self.get_name() >= other.get_name()

    def __cmp__(self, other):
        try:
            return cmp(self.get_name(), other.get_name())
        except:
            return True

    def __hash(self):
        return hash(self.get_name())

TCOUNTER = 0

class CommonThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        global TCOUNTER
        TCOUNTER = TCOUNTER + 1
        self.setName(TCOUNTER)
        #print 'creado: '+self.getName()
    
    def execute(self):
        raise NotImplementedError('CommonThread.execute() not implemented yet!')
    
    def run(self):
        while True:
            self.execute()
            time.sleep(0.1)
            #print 'ejecutando:'+self.getName()
            if not self.__started:
                #print 'matando:'+self.getName()
                break

    def start(self):
        try:
            self.__started = True
            threading.Thread.start(self)
        except Exception, ex:
            print ex
            pass

    def stop(self):
        self.__started = False