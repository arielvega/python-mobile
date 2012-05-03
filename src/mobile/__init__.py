#coding:utf-8
'''
Created on 04/08/2011

@author: Luis Ariel Vega Soliz (vsoliz.ariel@gmail.com)
@contact: Uremix Team (http://uremix.org)

'''

import serial, time, datetime, re, os, threading, math
import pdu
#from symbol import except_clause
from mobile.common import *
from mobile.common import KNOWNSERIALPORTS, EOL, EOF, RWSTORAGE, parse_CMGR_txt_to_sms, parse_txt_to_sms, split_sms_text, parse_txt_to_phonebook, parse_txt_to_phonebook_entry, get_os_port


__all__ = ['ATTerminalConnection', 'MobileDevice', 'MobilePhone']


def list_at_terminals(findlist = ['ttyUSB']):
    ''' Function that lists all the AT terminals connected to the computer '''
    atlist = []
    for interface in findlist:
        if interface in KNOWNSERIALPORTS:
            step = -1
            while step < 255:
                step = step + 1
                try:
                    attc = ATTerminalConnection(interface + str(step))
                    attc.open()
                    attc.set_timeout(0.01)
                    res = attc.send_command('AT')
                    if res <> None and ('OK' in res or 'AT' in res):
                        atlist.append(attc)
                        attc.set_timeout(None)
                    attc.close()
                except Exception, detail:
                    pass
    return atlist

class ATListener:
    def listen(self, event, source):
        raise NotImplementedError()

class ATTerminalConnection(CommonThread):
    ''' Represents a terminal who process AT commands '''
    def __init__(self, port = '/dev/ttyUSB0', atlistener = None):
        CommonThread.__init__(self)
        self.__port_name = get_os_port(port)
        self.__is_open = False
        self.__port = None
        self.__timeout = None
        self.__atlistener = atlistener
        self.__started = False
        self.__mutex = threading.Lock()

    def get_port_name(self):
        return self.__port_name

    def exec_command(self, command):
        if command <> EOF:
            self.send_direct_command(command + EOL, False)
        else:
            self.send_direct_command(command, False)
        time.sleep(0.01)

    def send_command(self, command, response = True):
        if response:
            self.clear_buffer()
        if command <> EOF:
            return self.send_direct_command(command + EOL, response)
        else:
            return self.send_direct_command(command, response)

    def send_direct_command(self, command, response = False):
        if(self.is_open()):
            #print '::::::::::::::::::::::::::::::::::::::::::::::::'
            self.__mutex.acquire()
            #print 'bloquea send_direct_command'
            self.__port.write(command)
            #c = command.replace('\r','')
            #c = c.replace('\n','')
            if response:
                res = self.read_buffer()
                self.__mutex.release()
                #print 'desbloquea send_direct_command'
                #r = res.replace('\r','')
                #r = r.replace('\n','')
                #print c+' :: '+r
                return res
            else:
                #print c
                self.__mutex.release()
                #print 'desbloquea send_direct_command'
                pass

    def execute(self):
        self.__mutex.acquire()
        #print 'bloquea run'
        self.read_buffer()
        self.__mutex.release()

    def stop(self):
        if self.__atlistener <> None:
            self.__atlistener.stop()
        CommonThread.stop(self)

    def read_buffer(self):
        if (self.__port == None) or not self.is_open():
            return
        res = ''
        a = time.time()
        b = time.time()
        while self.__port.inWaiting() or not self.__is_acknowledge_response(res):
            buff = self.__port.readline()
            buff = buff.replace('\r\n', '')
            buff = buff.replace('\n', '')
            buff = buff.replace('\r', '')
            if not self.__is_status_response(buff):
                if self.__is_acknowledge_response(buff):
                    if len(res)==0:
                        res = buff
                    break
                else:
                    if len(buff)>0:
                        res = res + '\n' +buff
            else:
                res = self.__port.readline()
                res = res.replace('\r\n', '')
                res = res.replace('\n', '')
                res = res.replace('\r', '')
                if self.__is_message_response(buff):
                    while not self.__is_status_response(res):
                        if len(res)>0:
                            buff = buff + '\n' + res
                        res = self.__port.readline()
                        res = res.replace('\r\n', '')
                        res = res.replace('\n', '')
                        res = res.replace('\r', '')
                else:
                    if len(res)>0:
                        buff = buff + '\n' + res
                self.__process_status_response_(buff)
            if (self.__timeout == None) or ( (b-a) < self.__timeout ):
                b = time.time()
                time.sleep(0.00001)
            else:
                break
        return res

    def __process_status_response_(self, response):
        event = response
        source = {}
        if self.__atlistener <> None:
            self.__atlistener.listen(event, source)

    def __is_acknowledge_response(self, response):
        return ('OK' in response) or ('ERROR' in response) or ('COMMAND NOT SUPPORT' in response)

    def __is_status_response(self, response):
        return response.startswith('+CMT') or response.startswith('+CDS') or response.startswith('+CBM') or response.startswith('^') or response.startswith('+CUSD') or response.startswith('RING')

    def __is_message_response(self, response):
        return response.startswith('+CMT')

    def clear_buffer(self):
        if self.__port == None:
            return
        self.__mutex.acquire()
        #print 'bloquea clear_buffer'
        self.__port.flushInput()
        self.__mutex.release()
        #print 'desbloquea clear_buffer'

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
            self.stop()
            self.send_command(command, False)
            res = self.read_buffer()
            self.start()
            self.close()
        else:
            res = self.send_command(command)
        self.set_timeout(to)
        return 'OK' in res

    def set_atlistener(self, atlistener):
        self.__atlistener = atlistener

    def __str__(self):
        return self.__port_name

    def __repr__(self):
        return str(self)


class HuaweiATListener(ATListener, CommonThread):
    def __init__(self, device):
        CommonThread.__init__(self)
        self.__started = False
        self.__device = device
        self.__mutex = threading.Lock()
        self.__funcs = []
        self.start()

    def execute(self):
        self.__mutex.acquire()
        if len(self.__funcs)>0:
            for (f,arg) in self.__funcs:
                f(arg)
            self.__funcs = []
        self.__mutex.release()

    def listen(self, event, source):
        self.__mutex.acquire()
        self.__funcs.append((self.listen_event, event))
        self.__mutex.release()
        
    def listen_event(self, event):
        print '::::::::::::::::::::::::'
        #print event
        if event.startswith('+CMTI:'):
            pos = event.split('\n')
            pos = pos[0].split(',')[-1]
            pos = int(pos)
            res = self.__device.get_sms(pos)
            print parse_CMGR_txt_to_sms((res, self.__device), pos)
            pass
        elif event.startswith('+CMT:'):
            txt = event[5:]
            txt = txt.strip().split('\n')
            while(txt.count('')>0):
                txt.remove('')
            if(len(txt) == 2):
                message = txt[-1]
            else:
                message = '\n'.join(txt[1:])
            txt = txt[0].strip().split(',')
            while(txt.count('')>0):
                txt.remove('')
            phone = txt[0].replace('"','')
            if(len(txt)>2):
                date = (txt[-2] + ', '+ txt[-1]).replace('"','')
            else:
                date=''
            sms = SMS(message, phone, date)
            print sms
            pass
        elif event.startswith('+CDS'):
            pass
        elif event.startswith('+CBM'):
            pass
        elif event.startswith('^RSSI:'):
            n = int(event.split(':')[-1].strip())
            x = int(math.ceil(float(float(n)*100)/float(31)))
            print 'signal: '+str(x)+'%'
            pass
        elif event.startswith('+CUSD:'):
            cusd = event.split(',')
            msg = pdu.decode(cusd[1].replace('"',''))
            print msg
            pass
        elif event.startswith('^DSFLOWRPT:'):
            stats1 = event[11:].strip().split(',')
            stats=[]
            for x in stats1:
                stats.append(float(int(x.strip(),16)))
            print 'uptime: '+str(int(stats[0]))+' s, up: '+str(round((stats[1]/8.0)/1024.0,1))+' KiB/s, down: '+str(round((stats[2]/8.0)/1024.0,1))+' KiB/s, sent: '+str(round((stats[3]/1024.0)/1024.0,1))+' MiB, recv: '+str(round((stats[4]/1024.0)/1024.0,1))+' MiB, uplink:'+str(round(stats[5]/1024.0,1))+' KiB/s, downlink:'+str(round(stats[6]/1024.0,1))+' KiB/s'
            pass
        elif event.startswith('^MODE:'):
            mode = event[6:].strip().split(',')
            modeinfo={}
            mode[0] = int(mode[0].strip())
            if len(mode)>1:
                mode[1] = int(mode[1].strip())
            else:
                mode.append(0)

            if mode[0]==0:
                modeinfo['net']='No service'
            elif mode[0]==1:
                modeinfo['net']='AMPS'
            elif mode[0]==2:
                modeinfo['net']='CDMA'
            elif mode[0]==3:
                modeinfo['net']='GSM/GPRS'
            elif mode[0]==4:
                modeinfo['net']='HDR'
            elif mode[0]==5:
                modeinfo['net']='WCDMA'
            elif mode[0]==6:
                modeinfo['net']='GPS'
            else:
                modeinfo['link']='Unknow'
            
            if mode[1]==0:
                modeinfo['link']='No service'
            elif mode[1]==1:
                modeinfo['link']='GSM'
            elif mode[1]==2:
                modeinfo['link']='GPRS'
            elif mode[1]==3:
                modeinfo['link']='EDGE'
            elif mode[1]==4:
                modeinfo['link']='WCDMA'
            elif mode[1]==5:
                modeinfo['link']='HSDPA'
            elif mode[1]==6:
                modeinfo['link']='HSUPA'
            elif mode[1]==7:
                modeinfo['link']='HSDPA/HSUPA'
            elif mode[1]==8:
                modeinfo['link']='TD-SCDMA'
            elif mode[1]==9:
                modeinfo['link']='HSPA+'
            else:
                modeinfo['link']='Unknow'

            print modeinfo
            pass
        elif event.startswith('RING'):
            pass


class MobileDevice(ATListener):
    ''' Represents a mobile device, this is the base class of a mobile phone '''
    def __init__(self, atport):
        self._port = atport
        atport.set_atlistener(HuaweiATListener(self))
        self._port.open()
        self.__manufacturer = ''
        self.__model = ''
        self.__imei = ''
        self.__operator = ''
        self.__mobile_network_code = ''
        self.__network_code = ''
        self.__country_code = ''
        self._listeners = {}
        self._listeners['new_sms'] = []
        self._listeners['change_rssi'] = []
        self._listeners['new_ussd'] = []
        self._listeners['dataflow'] = []
        self._prepare()

    def emit(self, event, data):
        if event in self._listeners.keys():
            for listener in self._listeners[event]:
                listener(self)

    def get_events(self):
        return self._listeners.keys()

    def connect(self, event, listener):
        if event in self._listeners.keys():
            self._listeners[event].append(listener)

    def disconnect(self, event, listener):
        if event in self._listeners.keys():
            index = self._listeners[event].index(listener)
            if index >= 0:
                del(self._listeners[event][index])

    def __eq__(self, other):
        return repr(self) == repr(other)

    def listen(self, event, source):
        self.emit(event, source)

    def _prepare(self):
        self._port.exec_command('AT+CFUN=1')
        self._port.exec_command('ATE0')
        self._port.exec_command('AT+CMGF=1')
        self._port.exec_command('AT+CPMS="MT","MT","MT"')
        self._port.exec_command('AT+COPS=0,0')
        self._port.exec_command('AT^SYSCFG=2,0,3FFFFFFF,1,3')
        self._port.exec_command('AT+CNMI=2,1,2,2,0')
        #self._port.exec_command('AT+CNMI=1,2,2,2,0')
        self._port.clear_buffer()

    def get_manufacturer(self):
        if self.__manufacturer == '':
            self.__manufacturer = self._port.send_command('AT+CGMI')
            self.__manufacturer = self.__manufacturer.replace('\n', '')
            self.__manufacturer = self.__manufacturer.replace('\r', '')
        return self.__manufacturer

    def get_model(self):
        if self.__model == '':
            self.__model = self._port.send_command('AT+CGMM')
            self.__model = self.__model.replace('\n', '')
            self.__model = self.__model.replace('\r', '')
        return self.__model

    def get_imei(self):
        if self.__imei == '':
            self.__imei = self._port.send_command('AT+CGSN')
        return self.__imei

    def get_operator(self):
        if self.__operator == '':
            self._port.exec_command('AT+COPS=0,1')
            res = self._port.send_command('AT+COPS?').split(',')
            self.__operator = res[-2].replace('"','')
        return self.__operator

    def get_mobile_network_code(self):
        if self.__mobile_network_code == '':
            self._port.send_command('AT+COPS=0,2')
            res = self._port.send_command('AT+COPS?').split(',')
            res = res[-2].replace('"','')
            self.__network_code = res[3:]
            self.__mobile_network_code = res
            self.__country_code = res[:3]
        return self.__mobile_network_code

    def get_network_code(self):
        if self.__network_code == '':
            self._port.send_command('AT+COPS=0,2')
            res = self._port.send_command('AT+COPS?').split(',')
            res = res[-2].replace('"','')
            self.__network_code = res[3:]
            self.__mobile_network_code = res
            self.__country_code = res[:3]
        return self.__network_code

    def get_country_code(self):
        if self.__country_code == '':
            self._port.send_command('AT+COPS=0,2')
            res = self._port.send_command('AT+COPS?').split(',')
            res = res[-2].replace('"','')
            self.__network_code = res[3:]
            self.__mobile_network_code = res
            self.__country_code = res[:3]
        return self.__country_code

    def get_signal_strenght(self):
        pass

    def create_sms(self, message, phone):
        return SMS(message, phone, device = self)

    def send_sms(self, message, phone = None):
        try:
            if isinstance(message, str) and phone == None:
                return False
            if isinstance(message, SMS):
                phone = message.get_phone_number()
                message = message.get_message()
            message = split_sms_text(message)
            for text in message:
                self._port.exec_command('AT+CMGS="'+str(phone)+'"')
                self._port.exec_command(text)
                self._port.send_direct_command(EOF)
            return True
        except:
            return False

    def _list_sms(self, phone , memory = 'ALL'):
        self._port.clear_buffer()
        res = self._port.send_command('AT+CMGL="'+memory+'"')
        res = res.split('+CMGL:')
        while(res.count('\r\n')>0):
            res.remove('\r\n')
        res = map(parse_txt_to_sms, [(x,y) for x in res for y in [self]])
        while res.count(None) > 0:
            res.remove(None)
        if phone <> None:
            res = [sms for sms in res if sms.get_phone_number() == phone]
        res.sort()
        return res

    def list_sms(self, phone = None):
        return self._list_sms(phone)

    def list_new_sms(self, phone = None):
        return self._list_sms(phone, 'REC UNREAD')

    def list_old_sms(self, phone = None):
        return self._list_sms(phone, 'REC READ')

    def list_unsended_sms(self, phone = None):
        return self._list_sms(phone, 'STO UNSENT')

    def list_sended_sms(self, phone = None):
        return self._list_sms(phone, 'STO SENT')

    def delete_sms(self, sms):
        if isinstance(sms, SMS):
            sms = sms.get_position()
        self._port.exec_command('AT+CMGD='+str(sms))

    def get_sms(self, index):
        self._port.clear_buffer()
        res = self._port.send_command('AT+CMGR='+str(index)+'')
        return parse_CMGR_txt_to_sms((res, self), index)

    def power_on(self):
        self._port.open()
        self._prepare()

    def power_off(self):
        self._port.close()

    def exec_command(self, cmd):
        return self._port.send_command('AT' + cmd)



class MobilePhone(MobileDevice):
    ''' Represents a mobile phone, it has methods for make and response a call '''

    def __init__(self, atport):
        MobileDevice.__init__(self, atport)
        self._port.set_timeout(0.5)
        #self._port.set_timeout(None)

    def _get_storage(self, storage = None):
        oldstorage = None
        if storage <> None:
            oldstorage = self._get_storage()
            self._port.exec_command('AT+CPBS="'+ storage +'" ')
        res = self._port.send_command('AT+CPBS? ')
        res = res.split('+CPBS:')
        while(res.count('\r\n')>0):
            res.remove('\r\n')
        res = parse_txt_to_phonebook((res[0], self))
        if oldstorage <> None:
            self._port.exec_command('AT+CPBS="'+ oldstorage.get_location() +'" ')
        return res

    def _get_phonebook(self, storage = None):
        oldstorage = None
        if storage <> None:
            oldstorage = self._get_storage()
            self._port.exec_command('AT+CPBS="'+ storage +'" ')
        res = self._get_storage()
        res.add_entries(self._get_phonebook_entries())
        if oldstorage <> None:
            self._port.exec_command('AT+CPBS="'+ oldstorage.get_location() +'" ')
        return res

    def _get_phonebook_entries(self, storage = None):
        if isinstance(storage, str):
            storage = self._get_storage(storage)
        oldstorage = None
        if storage <> None:
            oldstorage = self._get_storage()
            self._port.exec_command('AT+CPBS="'+ storage.get_location() +'" ')
        else:
            storage = self._get_storage()
        res = self._port.send_command('AT+CPBR=1,' + str(storage.get_capacity()) )
        res = res.split('+CPBR:')
        while(res.count('\r\n')>0):
            res.remove('\r\n')
        res = map(parse_txt_to_phonebook_entry, [(x,y) for x in res for y in [storage]])
        if oldstorage <> None:
            self._port.exec_command('AT+CPBS="'+ oldstorage.get_location() +'" ')
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
        self._port.exec_command('AT+CPBS="'+storage+'"')
        self._port.exec_command('AT+CPBW='+str(entry.get_position())+','+entry.get_phone_number(),','+str(entry.get_type())+',"'+entry.get_name()+'"')
        self._port.exec_command('AT+CPBS="'+oldstorage.get_location()+'"')

    def _delete_phonebook_entry(self, storage, entry):
        oldstorage = self._get_storage()
        if storage not in RWSTORAGE:
            return
        self._port.exec_command('AT+CPBS="'+storage+'"')
        self._port.exec_command('AT+CPBW='+str(entry.get_position()))
        self._port.exec_command('AT+CPBS="'+oldstorage.get_location()+'"')

    def call(self, phone):
        to = self._port.get_timeout()
        self._port.set_timeout(7)
        res = self._port.send_direct_command('ATD'+phone+'\r', True)
        self._port.set_timeout(to)
        return res.count('OK')>0 or res.count('NO CARRIER')>0

    def USSD_command(self, command):
        ccommand = pdu.encode(command)
        self.exec_command('+CUSD=1,'+ccommand+',15')

    def set_apn(self, apn):
        self.exec_command('AT+CGDCONT=1,"IP","'+apn+'"')

    def get_apn(self, apn):
        return self.send_command('AT+CGDCONT?')


if __name__ == '__main__':
    terms = list_at_terminals() # list available terminals :D
    print terms
    #print pdu.decode('07919571870300F70404A078780000212020002181004CD3309BFC06A5DDF3BA393D4E97DDF432081E968741F272989DD687E5207618449787DDF3F0789C7EBB59A0B49B5E76D3CBA0F1DB0DAABB41EDB79BFE06B5CBEEB7DC05')
    #print pdu.decode('C274D96D2FBBD3E437280CA2A6CF6FD014FD86C3D3EE330B5466A7CF65D01B3E4EBFDD3A8522E66A41C3F17A999E3EBFE70A99AB452D83E2F532393CA79741F3B41B349697C969FAFBA798B95ACBF47BBE7E83A8C9E3534173B582637ADA1E064DC36CF21B0495BFDB6F05')
    #print pdu.encode('مرحبا')
    
    #+CUSD: 1,"C274D96D2FBBD3E437280CA2A6CF6FD014FD86C3D3EE330B5466A7CF65D01B3E4EBFDD3A8522E66A41C3F17A999E3EBFE70A99AB452D83E2F532393CA79741F3B41B349697C969FAFBA798B95ACBF47BBE7E83A8C9E3534173B582637ADA1E064DC36CF21B0495BFDB6F05",15
    
    #print pdu.decode('0404A078780000212020002181004CD3309BFC06A5DDF3BA393D4E97DDF432081E968741F272989DD687E5207618449787DDF3F0789C7EBB59A0B49B5E76D3CBA0F1DB0DAABB41EDB79BFE06B5CBEEB7DC05')
    if len(terms)>0:
        mobile = MobilePhone(terms[-1]) # create a mobile phone with the last terminal
        terms[-1].start()
        #sms = mobile.create_sms('saldo', 2255) # we create a SMS
        #sms = mobile.create_sms('4040901570989', 171) # cargamos al chip
        #sms = mobile.create_sms('hora', 4646) # habilitamos internet
        #sms.send() # yeah babe! :D
        #l =  mobile.list_sms('2255')
        #l =  mobile.list_new_sms('2255')
        #print l
        #for msg in l:
        #    msg.delete()
        #print mobile.get_manufacturer()
        #print mobile.get_model()
        #print mobile.get_country_code()
        #print mobile.get_network_code()
        #print mobile.get_phonebook()
        ##mobile.USSD_command('*222#')
        #print 'duerme'
        #time.sleep(5)
        #print 'despierta'
        #mobile.USSD_command('1')
        #print mobile.get_sms(3)
        #print mobile.list_sms() # watch the sms's on the phone :D
        #mobile._prepare()
        #print mobile.call('70927261')
        #print mobile.exec_command('+CPMS="SM","SM","SM"')
        #print mobile.exec_command('+CMGL="REC READ"')
        #print mobile.exec_command('+CLAC') OBTIENE LA LISTA DE COMANDOS AT SOPORTADOS POR EL TELEFONO
        #print mobile.exec_command('+COPS=0,0')
        #print mobile.exec_command('+CUSD=1,'+pdu.encode('*105#')+',15')