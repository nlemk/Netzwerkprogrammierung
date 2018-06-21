#!/usr/bin/env python

import socket

host = 'localhost'
port = 9000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.bind((host,port))
s.listen(socket.SOMAXCONN)

try:
	while True:	
		inSocket, addr = s.accept();
		print("Connection with Client {}".format(addr))
		
		inSocket.send(bytes("Server accepts connection",'utf-8'))
		inSocket.close()
		
finally:
	s.close()
	
