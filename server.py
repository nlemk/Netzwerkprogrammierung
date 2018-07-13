#!/usr/bin/env python

import socket
import json
import time 
from threading import Thread
from package import Package
from distutils.version import LooseVersion

host = 'localhost'
port = 9000
newPort = port+1
count = 0
clientList = []
connectedClients = []

package1 = Package("test1", "1.0.8", "http://localhost:9000/resources/myclient_1.0.zip")
package2 = Package("useless Package", "1.0.0", "http://localhost:9000/resources/nothing.zip")
package3 = Package("package1", "2.12.3", "http://localhost:9000/resources/importantStuff.zip")
package4 = Package("lastPackage", "4.0.6", "http://localhost:9000/resources/fancy.zip")

packageList = [package1, package2, package3, package4]


def upgrade(package):
	#json string erstellen
	strings = {"Upgrade":"upgrade test"}
	strings = json.dumps(strings)
	return strings



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


def heartbeat(newSocket):
	connected = True

	global count
	json_iD = None
	while connected:
		print("thread" + str(count))
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
					print(message["Client-ID"])
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
				if "Upgrade" in message:
					print("upgrade")
					upgradeMessage = upgrade(message["Upgrade"]["Package"])
					time.sleep(0.2)
					newSocket.send(bytes(upgradeMessage,'utf-8'))
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
	
