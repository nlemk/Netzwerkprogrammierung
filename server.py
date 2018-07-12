#!/usr/bin/env python

import socket
import json
import time 
from threading import Thread


host = 'localhost'
port = 9000
newPort = port+1
count = 0
clientList = []
connectedClients = []

def heartbeat(newSocket):
	connected = True
	global count
	json_iD = None
	while connected:
		print("thread" + str(count))
		count+=1
		try:
			beat = newSocket.recv(40)
			if (len(beat) > 0):
				iD = beat.decode('utf-8')
				json_iD = json.loads(iD)
				print(json_iD["Client-ID"])
			else:
				connected = False
				print("disconnected")
				
			time.sleep(0.5)
		except ConnectionResetError:
			print("Connection lost")
		except json.decoder.JSONDecodeError:
			connected = True
	print("end")


def anmelden(s):
	#verbinden und anmelden
	connect = False
	global clientList, newPort
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
		#neuen Socket zum Verbinden benutzen
		#alten frei geben
		newPortInfo = json.dumps({"newPort" : newPort})
		inSocket.send(bytes(newPortInfo,'utf-8'))
		connectThread = Thread(target=newConnection, args=(newPort,))
		newPort += 1
		#check if in clientList
		registered = False
		for x in range (0, len(clientList)):
			if json_info["Client-ID"] == clientList[x]["Client-ID"]:
				registered = True
		if not registered:
			clientList.append(json_info)
		connectThread.start()
		inSocket.close()
		
		s.listen(socket.SOMAXCONN)
		anmelden(s)
	finally:
		s.close()

def newConnection(newport):
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	newsock.bind((host,newport))
	newsock.listen(socket.SOMAXCONN)
	try:
		newSocket, addr = newsock.accept();
		newSocket.send(bytes("Server changed Socket",'utf-8'))

		t = Thread(target=heartbeat, args=(newSocket,))	
		t.start()
		while t.is_alive():	
			print(len(clientList))		
			time.sleep(0.5)

	finally:
		newSocket.close()
		newsock.close()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.bind((host,port))
s.listen(socket.SOMAXCONN)

anmelden(s)

'''connect = False
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
		time.sleep(0.5)
	
	#inSocket.close()
		
finally:
	s.close()'''
	
