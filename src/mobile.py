'''
Created on 04/08/2011

@author: Luis Ariel Vega Soliz (vsoliz.ariel@gmail.com)
@contact: Uremix Team (http://uremix.org)

'''

import serial, time, datetime


__ALL__ = ['PhoneBook', 'PhoneBookEntry', 'SMS', 'ATTerminalConnection', 'MobileDevice', 'MobilePhone']

EOL = '\r\n'
EOF = chr(26)
RWSTORAGE = ['SM', 'ME', 'MT']
KNOWNSERIALPORTS = ['ttyS', 'ircomm', 'ttyUB', 'ttyUSB', 'rfcomm', 'ttyACM']
''' # Serial device to which the mobile device may be connected:
/dev/ttyS*    for serial port, 
/dev/ircomm*  for IrDA,
/dev/ttyUB*   for Bluetooth (Bluez with rfcomm running),
/dev/ttyUSB*  for USB,
/dev/rfcomm*  Bluetooth serial port and
/dev/ttyACM*  for USB ACM 

from: http://www.lugmen.org.ar/pipermail/lug-list/2005-April/035245.html
'''

def list_at_terminals(findlist = ['ttyUSB']):
    ''' Function that lists all the AT terminals connected to the computer '''
    atlist = []
    for interface in findlist:
        if interface in KNOWNSERIALPORTS:
            step = -1
            while step < 255:
                step = step + 1
                try:
                    attc = ATTerminalConnection('/dev/' + interface + str(step))
                    attc.set_timeout(0.01)
                    attc.open()
                    res = attc.send_command('AT')
                    if 'OK' in res:
                        attc.close()
                        atlist.append(attc)
                        attc.set_timeout(None)
                except Exception, e:
                    pass
    return atlist

def _parse_txt_to_sms((txt, device)):
    txt = txt.strip().split('\r\n')
    if (txt.count('ERROR')>0):
        return
    while(txt.count('OK')>0):
        txt.remove('OK')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) <> 2):
        return
    message = txt[-1]
    txt = txt[0].strip().split(',')
    while(txt.count('')>0):
        txt.remove('')
    pos = txt[0].replace('"','')
    memory = txt[1].replace('"','')
    phone = txt[2].replace('"','')
    date = (txt[3] +', '+ txt[4]).replace('"','')
    return SMS(message, phone, date, pos, memory, device)

def _parse_txt_to_phonebook_entry((txt, memory)):
    txt = txt.strip().split('\r\n')
    if (txt.count('ERROR')>0):
        return
    while(txt.count('OK')>0):
        txt.remove('OK')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) == 0):
        return
    txt = txt[0].strip().split(',')
    while(txt.count('')>0):
        txt.remove('')
    pos = txt[0].replace('"','')
    phone = txt[1].replace('"','')
    type = txt[2].replace('"','')
    name = txt[3].replace('"','')
    return PhoneBookEntry(name, phone, pos, type, memory)

def _parse_txt_to_phonebook((txt, device)):
    txt = txt.strip().split('\r\n')
    if (txt.count('ERROR')>0):
        return
    while(txt.count('OK')>0):
        txt.remove('OK')
    while(txt.count('')>0):
        txt.remove('')
    if(len(txt) == 0):
        return
    txt = txt[0].strip().split(',')
    while(txt.count('')>0):
        txt.remove('')
    location = txt[0].replace('"','')
    capacity = txt[2].replace('"','')
    return PhoneBook(location, capacity, device)



class PhoneBook:
    ''' Represents a phonebook '''
    def __init__(self, location, capacity, device):
        self.__location = location
        self.__capacity = int(capacity)
        self.__device = device
        self.__entries = []

    def get_location(self):
        return self.__location

    def get_used(self):
        res = 0
        for e in self.__entries:
            if e <> None:
                res = res + 1
        return res

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
            if self.__entries[entry.get_position()] <> None :
                if self.__entries[entry.get_position()] <> entry :
                    entry.set_position(self.get_free_position())
                else:
                    return
            self.__entries[entry.get_position()] = entry

    def get_free_position(self):
        i = 0
        while i < self.__capacity:
            if self.__entries[i] <> None:
                return i + 1
            i = i + 1
        return None

    def create_entry(self, name, phone):
        return PhoneBookEntry(name, phone, self.get_free_position(), phonebook = self)

    def delete_entry(self, entry):
        pass

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
                self.__entries[entry.get_position()] = entry

    def __str__(self):
        return 'Storage: ' + self.__location + '\nMax: ' + str(self.__capacity) + '\nUsed: ' + str(self.get_used()) + '\nEntries:\n' + '\n'.join([str(i) for i in self.__entries])

    def __repr__(self):
        return str(self)



class PhoneBookEntry:
    ''' It represents a entry on the phonebook '''
    def __init__(self, name, phone, pos = -1, atype = 129, phonebook = None):
        self.__name = name
        self.__phone_number = phone
        self.__position = int(pos) - 1
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
        pass

    def save(self):
        self.__phonebook.save_entry(self)

    def __str__(self):
        return self.__name + ': ' + str(self.__phone_number)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        try:
            return self.__name == other.get_name() and self.__phone_number == other.get_phone_number() and self.__position == other.get_position() and self.__type == other.get_type()
        except:
            return False

    def __neq__(self, other):
        return not self.__eq__(other)



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
            return
        self.__device.send_sms(self)

    def delete(self):
        if self.__device == None:
            return
        self.__device.delete_sms(self)

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
        res = 'Phone: '+ str(self.__phone_number) +'\nMsg: '+ self.__message + '\nDate: '+ self.__date + '\nMemory: ' + self.__memory + '\nPosition: '+ str(self.__position) + '\n:::'
        return res

    def __repr__(self):
        return str(self)



class ATTerminalConnection:
    ''' Represents a terminal who process AT commands '''
    def __init__(self, port = '/dev/ttyUSB0'):
        self.__port_name = port
        self.__is_open = False
        self.__port = None
        self.__timeout = None

    def get_port_name(self):
        return self.__port_name

    def send_command(self, command, response = True):
        return self.send_direct_command(command +EOL, response)

    def send_direct_command(self, command, response = False):
        if(self.is_open()):
            self.__port.write(command)
            if response:
                res = self.read_buffer()
                return res

    def read_buffer(self):
        if self.__port == None:
            return
        res = ''
        a = time.time()
        b = time.time()
        while self.__port.inWaiting() or not self.__is_valid_response(res):
            buff = self.__port.readline()
            if not buff.startswith('^'):
                res = res + buff
            if (self.__timeout == None) or ( (b-a) < self.__timeout ):
                b = time.time()
                time.sleep(0.0001)
            else:
                break
        self.__port.flushInput()
        return res

    def __is_valid_response(self, response):
        return ('OK' in response) or ('ERROR' in response) or ('COMMAND NOT SUPPORT' in response)

    def clear_buffer(self):
        if self.__port == None:
            return
        self.__port.flushInput()

    def open(self):
        if (self.is_open()):
            return 
        try:
            if self.__port == None:
                self.__port = serial.Serial(self.__port_name)
            self.__port.open()
            self.__is_open = True
        except:
            raise

    def close(self):
        if (self.__port == None) or (not self.is_open()):
            return
        try:
            self.__port.close()
            self.__is_open = False
        except:
            pass

    def set_timeout(self, timeout):
        self.__timeout = timeout
        if self.__port <> None:
            self.__port.setTimeout(timeout)

    def get_timeout(self):
        return self.__timeout

    def is_open(self):
        return self.__is_open

    def exist_command(self, command, timeout = None):
        to = self.__timeout
        self.set_timeout(timeout)
        if not self.is_open():
            self.open()
            self.send_command(command, False)
            res = self.read_buffer()
            self.close()
        else:
            res = self.send_command(command)
        self.set_timeout(to)
        return '\r\nOK\r\n' in res

    def __str__(self):
        return self.__port_name

    def __repr__(self):
        return str(self)



class MobileDevice:
    ''' Represents a mobile device, this is the base class of a mobile phone '''
    def __init__(self, atport):
        self._port = atport
        self._port.open()

    def _prepare(self):
        self._port.send_command('ATE0')
        self._port.send_command('AT+CMGF=1')
        self._port.send_command('AT+CPMS="ME","ME","ME"')
        self._port.send_command('AT+COPS=0,0')

    def get_manufacturer(self):
        return self._port.send_command('AT+CGMI')

    def get_model(self):
        return self._port.send_command('AT+CGMM')

    def get_imei(self):
        return self._port.send_command('AT+CGSN')

    def create_sms(self, message, phone):
        return SMS(message, phone, device = self)

    def send_sms(self, message, phone = None):
        self._prepare()
        if isinstance(message, str) and phone == None:
            return
        if isinstance(message, SMS):
            phone = message.get_phone_number()
            message = message.get_message()
        to = self._port.get_timeout()
        self._port.set_timeout(None)
        self._port.send_command('AT+CMGS="'+str(phone)+'"', False)
        self._port.send_command(message,False)
        self._port.send_direct_command(EOF)        
        #self._port.clear_buffer()
        print self._port.read_buffer()
        self._port.set_timeout(to)

    def _list_sms(self, memory = 'ALL'):
        self._prepare()
        self._port.clear_buffer()
        res = self._port.send_command('AT+CMGL="'+memory+'"')
        res = res.split('+CMGL:')
        while(res.count('\r\n')>0):
            res.remove('\r\n')
        res = map(_parse_txt_to_sms, [(x,y) for x in res for y in [self]])
        return res

    def list_sms(self):
        return self._list_sms()

    def list_new_sms(self):
        return self._list_sms('REC UNREAD')

    def list_old_sms(self):
        return self._list_sms('REC READ')

    def delete_sms(self, sms):
        self._prepare()
        if isinstance(sms, SMS):
            sms = sms.get_position()
        print self._port.send_command('AT+CMGD='+str(sms))

    def get_operator(self):
        self._prepare()
        res = self._port.send_command('AT+COPS?').split(',')
        return res[-2].replace('"','')

    def get_signal_strenght(self):
        pass



class MobilePhone(MobileDevice):
    ''' Represents a mobile phone, it has methods for make and response a call '''

    def __init__(self, atport):
        MobileDevice.__init__(self, atport)
        self._port.set_timeout(0.5)

    def _get_storage(self, storage = None):
        self._prepare()
        oldstorage = None
        if storage <> None:
            oldstorage = self._get_storage()
            self._port.send_command('AT+CPBS="'+ storage +'" ')
        res = self._port.send_command('AT+CPBS? ')
        res = res.split('+CPBS:')
        while(res.count('\r\n')>0):
            res.remove('\r\n')
        res = _parse_txt_to_phonebook((res[0], self))
        if oldstorage <> None:
            self._port.send_command('AT+CPBS="'+ oldstorage.get_location() +'" ')
        return res

    def _get_phonebook(self, storage = None):
        self._prepare()
        oldstorage = None
        if storage <> None:
            oldstorage = self._get_storage()
            self._port.send_command('AT+CPBS="'+ storage +'" ')
        res = self._get_storage()
        res.add_entries(self._get_phonebook_entries())
        if oldstorage <> None:
            self._port.send_command('AT+CPBS="'+ oldstorage.get_location() +'" ')
        return res

    def _get_phonebook_entries(self, storage = None):
        self._prepare()
        if isinstance(storage, str):
            storage = self._get_storage(storage)
        oldstorage = None
        if storage <> None:
            oldstorage = self._get_storage()
            self._port.send_command('AT+CPBS="'+ storage.get_location() +'" ')
        else:
            storage = self._get_storage()
        res = self._port.send_command('AT+CPBR=1,' + str(storage.get_capacity()) )
        res = res.split('+CPBR:')
        while(res.count('\r\n')>0):
            res.remove('\r\n')
        res = map(_parse_txt_to_phonebook_entry, [(x,y) for x in res for y in [self._get_storage()]])
        if oldstorage <> None:
            self._port.send_command('AT+CPBS="'+ oldstorage.get_location() +'" ')
        return res

    def get_phonebook(self):
        return self._get_phonebook()

    def get_missed_calls(self):
        return self._get_phonebook('MC')

    def get_dialed_calls(self):
        return self._get_phonebook('DC')

    def get_received_calls(self):
        return self._get_phonebook('RC')

    def _save_phonebook_entry(self, storage, entry):
        oldstorage = self._get_storage()
        if storage not in RWSTORAGE:
            return
        self._port.send_command('AT+CPBS="'+storage+'"')
        self._port.send_command('AT+CPBW='+str(entry.get_position())+','+entry.get_phone_number(),','+str(entry.get_type())+',"'+entry.get_name()+'"')
        self._port.send_command('AT+CPBS="'+oldstorage.get_location()+'"')

    def call(self, phone):
        self._prepare()
        return self._port.send_command('ATD'+phone)



if __name__ == '__main__':
    terms = list_at_terminals() # list available terminals :D
    print terms
    if len(terms)>0:
        mobile = MobilePhone(terms[-1]) # create a mobile phone with the last terminal
        #sms = mobile.create_sms('jejejejeje', 70927261) # we create a SMS
        #sms.send() # yeah babe! :D
        print mobile.list_sms() # watch the sms's on the phone :D