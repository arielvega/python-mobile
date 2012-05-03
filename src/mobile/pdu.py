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
    while char_nr <= len(bits):
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
    while i < len(gsm) - 1:
        if str(ord(gsm[i])) in gsm_to_latin:
            latin += chr(gsm_to_latin[str(ord(gsm[i]))])
        else:
            latin += gsm[i]
        i += 1

    return latin