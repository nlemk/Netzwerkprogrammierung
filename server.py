#!/usr/bin/env python

import socket
import json
import time 
from threading import Thread
from package import Package
from distutils.version import LooseVersion
import select

host = 'localhost'
port = 9000
newPort = port+1
count = 0
clientList = []
connectedClients = []

package1 = Package("test1", "1.0.8", "http://localhost:9000/resources/myclient_1.0.tgz")
package2 = Package("useless Package", "1.0.0", "http://localhost:9000/resources/nothing.tgz")
package3 = Package("package1", "2.12.3", "http://localhost:9000/resources/importantStuff.tgz")
package4 = Package("lastPackage", "4.0.6", "http://localhost:9000/resources/fancy.tgz")

packageList = [package1, package2, package3, package4]


def checkForUpdate(clientPackages):
	#falls keine Packages installiert sind
	updateList = []
	if not bool(clientPackages):
		updateList.append("Everything up to date")
		return updateMessage
	else:
		for x in range(0,len(clientPackages)):
			for y in range(0, len(packageList)):
				pack = clientPackages["Package" + str(x+1)]
				if (pack["Packagename"] == packageList[y].name):
					if LooseVersion(pack["Version"]) < LooseVersion(packageList[y].version):
						updateList.append(packageList[y].name)
		return updateList


def heartbeat(newSocket, clientID):
	connected = True
	global count
	json_iD = None
	while connected:
		#print("thread" + str(count))
		count+=1
		try:
			#heartbeat setzt aus funktion wartet auf eingabe -> beendet nicht
			# timer oder timeout einbauen, eartet max 5sek auf eingabe, keine da -> disconnect
			# listen auslagern in neuen Thread
			# compare der packages -> liste abschicken
			
			message = newSocket.recv(1000)
			if (len(message) > 0):
				message = message.decode('utf-8')
				message = json.loads(message)
				if "Client-ID" in message:
					connected = True
					#print(message["Client-ID"])
				if "Packages" in message:
					if not bool(message["Packages"]):
						upd = {"Updates" : "Keine Updates vorhanden"}
					else:
						updater = checkForUpdate(message["Packages"])
						if len(updater) > 0:
							updates = {}
							for x in range(0, len(updater)):
								updates.update({"update" + str(x+1) : updater[x]})
							upd = {"Updates" : updates}
						else:
							upd = {"Updates" : "Keine Updates vorhanden"}
					upd = json.dumps(upd)
					time.sleep(0.5)
					newSocket.send(bytes(upd,'utf-8'))
			else:
				connected = False
				connectedClients.remove(clientID)
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
	global clientList, newPort, connectedClients
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
		connectThread = Thread(target=newConnection, args=(newPort,json_info["Client-ID"],))
		newPort += 1
		#check if in clientList
		registered = False
		for x in range (0, len(clientList)):
			if json_info["Client-ID"] == clientList[x]["Client-ID"]:
				registered = True
		if not registered:
			clientList.append(json_info)
		if json_info["Client-ID"] not in connectedClients:
			connectedClients.append(json_info["Client-ID"])
			print(connectedClients)
			connectThread.start()
		else:
			print("connection refused")
		inSocket.close()
		
		s.listen(socket.SOMAXCONN)
		anmelden(s)
	finally:
		s.close()

def newConnection(newport, clientID):
	global clientList
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	newsock.bind((host,newport))
	newsock.listen(socket.SOMAXCONN)
	try:
		newSocket, addr = newsock.accept();
		text = {"info" : "Server changed Socket"}
		text = json.dumps(text)
		newSocket.send(bytes(text,'utf-8'))
		time.sleep(0.5)
		newSocket.send(bytes("Send Client Data",'utf-8'))
		time.sleep(0.5)
		completeClientInfo = newSocket.recv(500)
		completeClientInfo = completeClientInfo.decode('utf-8')
		completeClientInfo = json.loads(completeClientInfo)
		for changer in range(0, len(clientList)):
			if clientList[changer]["Client-ID"] == completeClientInfo["Client-ID"]:
				clientList[changer] = completeClientInfo
				break
		
		t = Thread(target=heartbeat, args=(newSocket,clientID,))	
		t.start()
		while t.is_alive():	
			#print(len(clientList))		
			time.sleep(0.5)

	finally:
		newSocket.close()
		newsock.close()


def listen():
	while True:
		action = input()
		action = action.split(" ")
		if action[0] == "show":
			found = False
			for x in clientList:
				if action[1] == x["Client-ID"]:
					print("Hostname  : " + x["Hostname"])
					print("Client-ID : " + x["Client-ID"])
					print("IP        : " + x["IP"])
					print("Alive     : " + x["Alive"])
					print("Datum     : " + x["Datum"])
					print("Info      : ")
					#Info
					info = x["Info"]
					#CPU
					print("\t    CPU-Info:")
					cpu = info["CPU-Info"]
					print("\t\t      Model name  : " + cpu["Model name"])
					print("\t\t      CPU(s)      : " + cpu["CPU(s)"])
					print("\t\t      Architecture: " + cpu["Architecture"])
					#RAM
					print("\t    RAM-Info:")
					ram = info["RAM-Info"]
					print("\t\t      MemTotal    : " + ram["MemTotal"])
					print("\t\t      MemFree     : " + ram["MemFree"])
					print("\t\t      MemAvailable: " + ram["MemAvailable"])
					#GPU
					print("\t    GPU-Info:")
					gpu = info["GPU-Info"]
					# check for german or english
					if " Beschreibung" in gpu :
						print("\t\t      Beschreibung :" + gpu[" Beschreibung"])
						print("\t\t      Hersteller   :" + gpu[" Hersteller"])
						print("\t\t      Produkt      :" + gpu[" Produkt"])
						print("\t\t      Takt         :" + gpu[" Takt"])
					else : 
						print("\t\t      description :" + gpu[" description"])
						print("\t\t      vendor      :" + gpu[" vendor"])
						print("\t\t      product     :" + gpu[" product"])
						print("\t\t      clock       :" + gpu[" clock"])
					found = True
					break
			if not found:
				print("Client nicht gefunden")
		if action[0] == "list":	
			if len(clientList) == 0:
				print("Es hat sich noch kein Client mit dem Server verbunden")
			else:
				print("Hostname \t\t Client-ID")
				for x in clientList:
					print(x["Hostname"] + " \t\t " + x["Client-ID"])
	

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.bind((host,port))
s.listen(socket.SOMAXCONN)

listener = Thread(target=listen)
listener.start()
anmelden(s)

