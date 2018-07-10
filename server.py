#!/usr/bin/env python

import socket
import json
import time 
from threading import Thread 

count = 0
clientList = []


def heartbeat():
	connected = True
	global count
	while connected:
		print("thread" + str(count))
		count+=1
		beat = inSocket.recv(40)
		if (len(beat) > 0):
			iD = beat.decode('utf-8')
			json_iD = json.loads(iD)
			print(json_info["Client-ID"])
		else:
			connected = False
			clientList.remove(json_info["Client-ID"])
			print("disconnected")
		time.sleep(0.5)

host = 'localhost'
port = 9000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.bind((host,port))
s.listen(socket.SOMAXCONN)

connect = False
try:
	while not connect:	
		inSocket, addr = s.accept();
		print("Connection with Client {}".format(addr))
		
		inSocket.send(bytes("Server accepts connection",'utf-8'))
		#inSocket.close()
		connect = True
		
	clientInfo = inSocket.recv(500)		
	if (len(clientInfo) > 0):
		info = clientInfo.decode('utf-8')
		print(info)
		json_info = json.loads(info)
		print(json_info["Client-ID"])
	clientList.append(json_info["Client-ID"])
	t = Thread(target=heartbeat)
	t.start()
	while len(clientList) > 0:
		print(clientList)
		time.sleep(4)
	#print("Wann kommt das hier dran")
	
	inSocket.close()
		
finally:
	s.close()
	
