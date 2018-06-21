#!/usr/bin/env python

import socket

host = 'localhost'
port = 9000

#connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.connect((host,port))

while True:
	recievedbytes = s.recv(50)
	if (len(recievedbytes) == 0):
		break;
	print(recievedbytes.decode('utf-8'))

s.close()
