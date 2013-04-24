#!/usr/bin/env python

############################################################################
#    Copyright (C) 2006 by Costin Stroie                                   #
#    cstroie@users.sourceforge.net                                         #
#                                                                          #
#    This program is free software; you can redistribute it and/or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

# Credits to:
#    Dave Berkeley <dave@rotwang.co.uk> for the pysms project
#    Dominik Pytlewski <d.pytlewski@gazeta.pl> for DoomiN's Phone Manager program


# Hex to dec conversion array
hex2dec = {'0':0, '1':1, '2':2, '3':3,'4':4, '5':5, '6':6, '7':7,'8':8, '9':9, 'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15 }

# GSM to ISO8859-1 conversion array
gsm_to_latin = {'0':64, '1':163, '2':36, '3':165,'4':232, '5':233, '6':249, '7':236,'8':242, '9':199,
        '11':216, '12':248,
        '14':197, '15':229, '16':0, '17':95,
        '18':0, '19':0, '20':0, '21':0, '22':0, '23':0, '24':0, '25':0, '26':0, '27':0,
        '28':198, '29':230, '30':223, '31':201,
        '36':164,
        '64':161,
        '91':196, '92':214, '93':209, '94':220, '95':167, '96':191,
        '123':228, '124':246, '125':241, '126':252, '127':224}


def hex2int(n):
    """
    Convert a hex number to decimal
    """
    c1 = n[0]
    c2 = n[1]

    c3 = (hex2dec[c1] * 16) + (hex2dec[c2])
    return int("%s" % c3)


def int2hex(n):
    """
    Convert a decimal number to hexadecimal
    """
    hex = ""
    q = n
    while q > 0:
        r = q % 16
        if   r == 10: hex = 'A' + hex
        elif r == 11: hex = 'B' + hex
        elif r == 12: hex = 'C' + hex
        elif r == 13: hex = 'D' + hex
        elif r == 14: hex = 'E' + hex
        elif r == 15: hex = 'F' + hex
        else:
            hex = str(r) + hex
        q = int(q/16)

    if len(hex) % 2 == 1: hex = '0' + hex
    return hex


def byteSwap(byte):
    """
    Swap the first and second digit position inside a hex byte
    """
    return "%c%c" % (byte[1], byte[0])

def decode(src):
    """
    Decode the 7-bits coded text to one byte per character
    """

    bits = ''

    i = 0
    l = len(src) - 1

    # First, get the bit stream, concatenating all binary represented chars
    while i < l:
        bits += char2bits(src[i:i+2])
        i += 2

    # Now decode those pseudo-8bit octets
    char_nr = 0
    i = 1

    tmp_out = ''
    acumul = ''
    decoded = ''
    l = len(bits)
    #while char_nr <= l:
    while char_nr < l:
        byte = bits[char_nr + i:char_nr + 8]
        tmp_out += byte + "+" + acumul + " "
        byte += acumul
        c = chr(bits2int(byte))
        decoded += c
        acumul = bits[char_nr:char_nr + i]
        i += 1
        char_nr += 8
        if i==8:
            i = 1
            char_nr
            decoded += chr(bits2int(acumul))
            acumul=''
            tmp_out += "\n"
    return gsm2latin(decoded)


def encode(src):
    """
    Encode ASCII text to 7-bit encoding
    """
    result = []
    count = 0
    last = 0
    for c in src:
        this = ord(c) << (8 - count)
        if count:
            result.append('%02X' % ((last >> 8) | (this & 0xFF)))
        count = (count + 1) % 8
        last = this
    result.append('%02X' % (last >> 8))
    return ''.join(result)


def char2bits(char):
    """
    Convert a character to binary.
    """

    inputChar = hex2int(char)
    mask = 1
    output = ''
    bitNo = 1

    while bitNo <= 8:
        if inputChar & mask > 0:
            output = '1' + output
        else:
            output = '0' + output
        mask = mask<<1
        bitNo += 1

    return output


def bits2int(bits):
    """
    Convert a binary string to a decimal integer
    """

    mask = 1
    i = 0
    end = len(bits) - 1

    result = 0
    while i <= end:
        if bits[end - i] == "1":
            result += mask
        mask = mask << 1
        i += 1

    return result


def gsm2latin(gsm):
    """
    Convert a GSM encoded string to latin1 (where available).
    TODO: implement the extension table introduced by char 27.
    """
    i = 0
    latin = ''
    l = len(gsm)
    #while i < len(gsm) - 1:
    while i < l:
        if str(ord(gsm[i])) in gsm_to_latin:
            latin += chr(gsm_to_latin[str(ord(gsm[i]))])
        else:
            latin += gsm[i]
        i += 1

    return latin

def semioctet2string(semistring):
    res =''
    for i in range(len(semistring)/2):
        byte = semistring[i*2:(i*2)+2]
        res = res + byteSwap(byte)
    return res

def pdudate2date(pdudate):
    pdudate = semioctet2string(pdudate)
    pdudate = pdudate[:2]+'/'+pdudate[2:4]+'/'+pdudate[4:6]+','+pdudate[6:8]+':'+pdudate[8:10]+':'+pdudate[10:12]+'+'+pdudate[12:]
    return pdudate

def smspdu2text_(smspdu):
    print smspdu
    smscnumberlen = hex2int(smspdu[ : 2])
    print 'smsc lenght: %d'%smscnumberlen
    SMSC = smspdu[2: 2+(smscnumberlen*2)]
    smscnumbertype = SMSC[:2]
    print 'sms center type: %s'%smscnumbertype
    smsc = semioctet2string(SMSC[2:])
    if (smscnumbertype == '91' and not smsc.startswith('+')):
        smsc = '+'+smsc
    if (smsc.endswith('F')):
        smsc = smsc[:-1]
    print 'sms center: %s'%smsc
    TPDU = smspdu[2+(smscnumberlen*2): ]
    fosmsdeliver = TPDU[ :2]
    print 'first octet deliver message: %s'%fosmsdeliver
    senderlen = hex2int(TPDU[2 : 2 +2])
    print 'sender lenght: %d'%senderlen
    if((senderlen % 2)<>0):
        senderlen = senderlen + 1
    sendernumbertype = TPDU[2+2 : 2+2 +2]
    print 'sender type: %s'%sendernumbertype
    sender = semioctet2string(TPDU[2+2+2 : 2+2+2 +senderlen])
    if (sendernumbertype == '91' and not sender.startswith('+')):
        sender = '+'+sender
    if (sender.endswith('F')):
        sender = sender[:-1]
    print 'sender: %s'%sender
    protocolID = TPDU[2+2+2+senderlen : 2+2+2+senderlen +2]
    print 'protocol id: %s'%protocolID
    encoding = TPDU[2+2+2+senderlen+2 : 2+2+2+senderlen+2 +2]
    print 'encoding scheme: %s'%encoding
    date = pdudate2date(TPDU[2+2+2+senderlen+2+2 : 2+2+2+senderlen+2+2 +14])
    print 'date: %s\n'%date
    print TPDU[2+2+2+senderlen+2+2+14 : 2+2+2+senderlen+2+2+14 +2]
    smslen = hex2int(TPDU[2+2+2+senderlen+2+2+14 : 2+2+2+senderlen+2+2+14 +2])
    print 'sms lenght: %d'%smslen
    #smstext = decode(smspdu[deliverpos+2+2+2+senderlen+2+2+14+2 : deliverpos+2+2+2+senderlen+2+2+14+2 +(smslen*2)])
    smstext = decode(TPDU[2+2+2+senderlen+2+2+14+2 :])
    print smstext

def smspdu2text(smspdu):
    print smspdu
    smsclen = hex2int(smspdu[ : 2])
    print 'smsc lenght: %d'%smsclen
    SMSC = smspdu[2: 2+(smsclen*2)]
    smsctype = SMSC[:2]
    print 'sms center type: %s'%smsctype
    smsc = semioctet2string(SMSC[2:])
    if (smsctype == '91' and not smsc.startswith('+')):
        smsc = '+'+smsc
    if (smsc.endswith('F')):
        smsc = smsc[:-1]
    print 'sms center: %s'%smsc


    TPDU = smspdu[2+(smsclen*2): ]
    fosmsdeliver = TPDU[ :2]
    print 'first octet deliver message: %s'%fosmsdeliver
    senderlen = hex2int(TPDU[2 : 2 +2])
    print 'sender lenght: %d'%senderlen
    if((senderlen % 2)<>0):
        senderlen = senderlen + 1
    sendertype = TPDU[2+2 : 2+2 +2]
    print 'sender type: %s'%sendertype
    sender = semioctet2string(TPDU[2+2+2 : 2+2+2 +senderlen])
    if (sendertype == '91' and not sender.startswith('+')):
        sender = '+'+sender
    if (sender.endswith('F')):
        sender = sender[:-1]
    print 'sender: %s'%sender
    proto = TPDU[2+2+2+senderlen : 2+2+2+senderlen +2]
    print 'protocol id: %s'%proto
    enc = TPDU[2+2+2+senderlen+2 : 2+2+2+senderlen+2 +2]
    print 'encoding scheme: %s'%enc
    date = pdudate2date(TPDU[2+2+2+senderlen+2+2 : 2+2+2+senderlen+2+2 +14])
    print 'date: %s\n'%date
    print TPDU[2+2+2+senderlen+2+2+14 : 2+2+2+senderlen+2+2+14 +2]
    smslen = hex2int(TPDU[2+2+2+senderlen+2+2+14 : 2+2+2+senderlen+2+2+14 +2])
    print 'sms lenght: %d'%smslen
    #smstext = decode(smspdu[deliverpos+2+2+2+senderlen+2+2+14+2 : deliverpos+2+2+2+senderlen+2+2+14+2 +(smslen*2)])
    smstext = decode(TPDU[2+2+2+senderlen+2+2+14+2 :])
    print smstext

if __name__=='__main__':
    #+CMGL: 1,1,,18 (viva)
    msg1 = '07919571700000F0A008A1072927160000213031320165690141'
    #+CMGL: 2,1,,72 (viva)
    msg2='07919571700060F50003A101F5000021609190401369415357704CAF87D93A980B065314F1701D2CD682D55A32584CA62086E9EFB90EE6820915D3F6FC280FD3D3731D4D310DB3ED617BDA1E9EEB6A0A'
    #+CMGL: 14,1,,23 (tigo)
    msg3='07919571870300F70408A12751563700002180018112946906D3793A0D8703'
    #+CMGL: 8,1,,25
    msg4='07919571870300F70408A0970006680000218001714573690932580D56ABC16438'
    msg6='07915892000000F0010B915892214365F700002180311061520021493A283D0795C3F33C88FE06CDCB6E32885EC6D341EDF27C1E3E97E72E'
    msg5='00010B915892214365F700002180311061520021493A283D0795C3F33C88FE06CDCB6E32885EC6D341EDF27C1E3E97E72E'
    msg7='07915892000000F001000B915892214365F700000021493A283D0795C3F33C88FE06CDCB6E32885EC6D341EDF27C1E3E97E72E'
    smspdu2text(msg5)