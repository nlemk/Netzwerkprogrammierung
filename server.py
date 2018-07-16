#!/usr/bin/env python

import socket
import json
import re
import time 
from threading import Thread
from package import Package
from distutils.version import LooseVersion
import select
import subprocess
import queue

host = 'localhost'
port = 9000
newPort = port+1
clientList = []
connectedClients = []
packageList=[]

def fillPackageList():
	"""Liest die Datei packages.json ein, erstellt daraus ein dict, erstellt mit diesen Werten ein Package und fuegt die in die Liste ein."""
	global PackageList	
	try:
		f = open("packages.json","r")
		packageFile = f.read()
		f.close()
	except FileNotFound:
		pass
	if len(packageFile) > 0:
		packages = json.loads(packageFile)
		for x in packages["packages"]:
			newPackage = Package(x["name"],x["version"],x["url"])
			packageList.append(newPackage)


def upgrade(package, queues):
	"""Sucht das Package, welches ein Upgrade benoetigt. Die Daten werden in ein dict eingegeben. Das dict wird in der queue gespeichert, um 
	es nach Ablauf des fuer diese Funktion erstellten Threads uebergeben zu koennen"""
	upgradePackage = None
	for x in packageList:
		if x.name == package:
			upgradePackage = x
	zipName = upgradePackage.url.replace("http://localhost:9000/","")
	f = open(zipName, "rb")
	zipData = f.read()
	f.close()
	try:
		zipData = zipData.decode('latin-1')
	except UnicodeDecodeError:
		zipData = zipData.decode('utf-8')
	data = {"Filename" : zipName,
		"Upgrade":"start",
	        "data" : zipData,
		"end": True}
	queues.put(data)


def checkForUpdate(clientPackages):
	"""Checkt die Versionen der Packages von Server und Client. Ist die Client-Version nicht die neueste, wird sie in die Liste der Updates 
	eingefuegt
	ClientPackages: Die Packete des Clients

	Gibt die Liste mit Packages zuruck, die ein Update verfuegbar haben"""
	#falls keine Packages installiert sind
	updateList = []
	if not bool(clientPackages):
		updateList.append("Everything up to date")
		return updateList
	else:
		for x in range(0,len(clientPackages)):
			for y in range(0, len(packageList)):
				pack = clientPackages["Package" + str(x+1)]
				if (pack["Packagename"] == packageList[y].name):
					if LooseVersion(pack["Version"]) < LooseVersion(packageList[y].version):
						updateList.append(packageList[y].name)
		return updateList

def setAlive(clientID):
	"""Setzt den Status Alive eines Clients auf False
	clientID: ID des Clients um ihn zu finden"""
	global clientList
	for x in clientList:
		if x["Client-ID"] == clientID:
			x["Alive"] = "False"

def heartbeat(newSocket, clientID):
	"""Einlesen aller gesendeten Daten, nach dem anmelden.Hier wird der heartbeat, das Update und das Upgrade behandelt.
	Endet der Heartbeat, aendert sich der Alive-Status und beendet den heartbeat-Thread
	newSocket: Der Socket wird zum Senden und Empfangen von Daten uebergeben
	clientID : ID des Clients. Falls seine ID nicht im heartbeat uebergeben werden kann. Dient in diesem Fall zur entfernung des Client aus 
		   der Liste der aktiven Clients"""
	connected = True
	global count,connectedClients
	json_iD = None
	data = ""
	filename = ""
	while connected:
		try:
			newSocket.settimeout(3)
			try:
				message = newSocket.recv(1000)
				if (len(message) > 0):
					message = message.decode('utf-8')
					message = json.loads(message)
					if "Client-ID" in message:
						connected = True
					if "Packages" in message:
						print("Check Updates für Client " + str(message["Client-ID"]))
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
								time.sleep(0.5)
								newSocket.send(bytes(json.dumps(newVersion),'utf-8'))
								break
					if "Upgrade" in message:
						queues = queue.Queue()
						upgradeThread = Thread(target = upgrade, args=(message["Upgrade"]["Package"],queues,))
						upgradeThread.start()
						time.sleep(0.2)
						upgradeThread.join()
						string = queues.get()
						strings = json.dumps(string)
						queues.task_done()
						time.sleep(0.2)
						print("Sende Upgrade an Client"  + str(message["Client-ID"]))
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
					connectedClients.remove(clientID)
					setAlive(clientID)
					print(str(clientID) + " disconnected")
			except socket.timeout:
				print(str(clientID) + " disconnected --timeout")
				connected = False
				connectedClients.remove(clientID)
				setAlive(clientID)
		except ConnectionResetError:
			connected = False
			connectedClients.remove(clientID)
			setAlive(clientID)
			print(str(clientID) + " Connection lost")
		except json.decoder.JSONDecodeError:
			connected = True


def anmelden(s):
	"""Der Server und der Client gehen eine Verbindung ein. Er schickt dem Client einen neuen Port, um den aktuellen Port fuer weitere 
	Anmeldungen zugaenglich zu lassen. Durch die erste Anmeldung an den Server registriert sich der Client
	
	s: Der Socket zum senden und empfangen"""
	#verbinden und anmelden
	connect = False
	global clientList, newPort, connectedClients
	try:
		while not connect:	
			inSocket, addr = s.accept();
			print("Connection with Client {}".format(addr))
	
			inSocket.send(bytes("Server accepts connection",'utf-8'))
			connect = True
		time.sleep(0.5)
		clientInfo = inSocket.recv(500)		
		if (len(clientInfo) > 0):
			info = clientInfo.decode('utf-8')
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
			connectThread.start()
		else:
			print("connection refused for Client" + str(json_info["Client-ID"]))
		inSocket.close()
		
		s.listen(socket.SOMAXCONN)
		anmelden(s)
	finally:
		s.close()

def newConnection(newport, clientID):
	"""Verbindung des Clients mit dem neuen Port. Der Server fragt hier nach detaillierteren Infos des Clients und sendet dem Client eine 
	Bestaetigung fuer die Verbindung. Startet den Thread fuer den Heartbeat
	newport  : Uebergabe des neuen Ports
	clientID : Zum Registrieren
	
	clientList: Liste aller Clients. Zum Registrieren"""
	global clientList
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	newsock.bind((host,newport))
	newsock.listen(socket.SOMAXCONN)
	try:
		newSocket, addr = newsock.accept();
		time.sleep(0.5)
		text = {"info" : "Server changed Socket"}
		text = json.dumps(text)
		newSocket.send(bytes(text,'utf-8'))
		time.sleep(1)
		text = {"info2" : "Send Client Data"}
		text = json.dumps(text)
		newSocket.send(bytes(text,'utf-8'))
		time.sleep(0.5)
		completeClientInfo = newSocket.recv(1000)
		completeClientInfo = completeClientInfo.decode('utf-8')
		completeClientInfo = json.loads(completeClientInfo)
		for changer in range(0, len(clientList)):
			if clientList[changer]["Client-ID"] == completeClientInfo["Client-ID"]:
				clientList[changer] = completeClientInfo
				break
		t = Thread(target=heartbeat, args=(newSocket,clientID,))	
		t.start()
		while t.is_alive():			
			time.sleep(0.5)

	finally:
		newSocket.close()
		newsock.close()


def listen():
	"""Behandelt die Eingabe des Servers.
	show id  : benoetigt die ID eines Clients. Zeigt dessen Informationen an(GPU,CPU,RAM,IP, etc.)
	list     : listet alle Clients auf, die sich verbunden haben. Zeigt auch nicht verbundene Clients
	alive id : benoetigt die ID eines Clients. Zeigt an, ob der Client noch verbunden ist"""
	while True:
		action = input()
		action = action.split(" ")
		if action[0] == "show":
			found = False
			if len(action) > 1 :
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
						print("\t\t      Model name   : " + cpu["Model name"])
						print("\t\t      CPU(s)       : " + cpu["CPU(s)"])
						print("\t\t      Architecture : " + cpu["Architecture"])
						#RAM
						print("\t    RAM-Info:")
						ram = info["RAM-Info"]
						print("\t\t      MemTotal     : " + ram["MemTotal"])
						print("\t\t      MemFree      : " + ram["MemFree"])
						print("\t\t      MemAvailable : " + ram["MemAvailable"])
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
			else:
				print("Gib eine ID hinter den Befehl show ein.")
		elif action[0] == "list":	
			if len(clientList) == 0:
				print("Es hat sich noch kein Client mit dem Server verbunden")
			else:
				print("Hostname \t\t Client-ID \t\t Status")
				for x in clientList:
					if x["Alive"] == "True":
						active = "connected"
					else: 
						active = "not connected"
					print(x["Hostname"] + " \t\t " + x["Client-ID"] + " \t\t " + active)
		elif action[0] == "alive":
			if len(action) > 1:
				found = False
				for x in clientList:
					if x["Client-ID"] == action[1]:
						if x["Alive"] == "True":
							alive = "connected"
						else:
							alive = "not connected"
						found = True
						print("Client " + str(action[1]) + " is " + alive)
				if not found:
					print("Client nicht gefunden")
			else:
				print("Gib eine ID hinter den Befehl alive ein.")
	


fillPackageList()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.bind((host,port))
s.listen(socket.SOMAXCONN)

listener = Thread(target=listen)
listener.start()
anmelden(s)
