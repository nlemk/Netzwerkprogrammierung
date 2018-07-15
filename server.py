#!/usr/bin/env python

import socket
import json
import re
import time 
from threading import Thread
from package import Package
from distutils.version import LooseVersion
import subprocess
import queue

host = 'localhost'
port = 9000
newPort = port+1
count = 0
clientList = []
connectedClients = []

'''package1 = Package("test1", "1.0.5", "http://localhost:9000/resources/myclient_1.0.zip")
package2 = Package("useless Package", "1.0.0", "http://localhost:9000/resources/nothing.zip")
package3 = Package("package1", "2.12.3", "http://localhost:9000/resources/importantStuff.zip")
package4 = Package("lastPackage", "4.0.6", "http://localhost:9000/resources/fancy.zip")

packageList = [package1, package2, package3, package4]'''

packageList=[]
try:
	f = open("packages.json","r")
	packageFile = f.read()
	f.close()
except FileNotFound:
	pass
if len(packageFile) > 0:
	packages = json.loads(packageFile)
	for x in packages["packages"]:
		print(x)
		newPackage = Package(x["name"],x["version"],x["url"])
		packageList.append(newPackage)


def upgrade(package, queues):
	print(package)
	upgradePackage = None
	for x in packageList:
		if x.name == package:
			upgradePackage = x
	zipName = upgradePackage.url.replace("http://localhost:9000/","")
	#zipName = zipName[len(zipName)-1]
	f = open(zipName, "rb")
	zipData = f.read()
	print(zipData)
	f.close()
	try:
		zipData = zipData.decode('latin-1')
	except UnicodeDecodeError:
		zipData = zipData.decode('utf-8')
	#zipData.replace('\r\n', '\\r\\n')
	data = {"Filename" : zipName,
		"Upgrade":"start",
	        "data" : zipData,
		"end": True}
	queues.put(data)




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
	data = ""
	filename = ""
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
				if len(data) > 0:
					if len(data) > 700:
						newStrings = {"Filename" : filename,
							       "Upgrade": "start",
							       "data"   : data[0:700],
							       "end"    : False}
						data = data[700:len(data)]
						filename = filename
					else:
						newStrings = {"Filename" : filename,
							       "Upgrade": "start",
							       "data"   : data,
							       "end"    : True}
						data =""
						filename = ""
					strings = json.dumps(newStrings)
					newSocket.send(bytes(strings,'utf-8'))
				if "message" in message:
					for x in packageList:
						if x.name == message["Name"]:
							newVersion = {"Version" : x.version}
							print(x.version)
							time.sleep(0.5)
							newSocket.send(bytes(json.dumps(newVersion),'utf-8'))
							break	
				if "Upgrade" in message:
					print("upgrade")
					queues = queue.Queue()
					upgradeThread = Thread(target = upgrade, args=(message["Upgrade"]["Package"],queues,))
					upgradeThread.start()
					time.sleep(0.2)
					upgradeThread.join()
					string = queues.get()
					strings = json.dumps(string)
					queues.task_done()
					print(strings)
					print("thread sollte laufen")
					time.sleep(0.2)
					if len(bytes(strings,'utf-8')) > 5000:
						newStrings = {"Filename" : string["Filename"],
								"Upgrade":"start",
	        						"data" : string["data"][0:700],
								"end": False}
						data = string["data"][700:len(string["data"])]
						filename = string["Filename"]
						strings = json.dumps(newStrings)
						newSocket.send(bytes(strings,'utf-8'))
					else:
						newSocket.send(bytes(strings,'utf-8'))
				
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
	
