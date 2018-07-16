#!/usr/bin/env python

import json
import socket
import platform
import subprocess
import re
import os
import time 
from uuid import getnode
from time import gmtime, strftime
from package import Package
import random
from threading import Thread

connected = False
pack = None
heartbeat = False
packageDict ={}
updateList = []
upgrade = []

def changeVersion(newVersion, packageName):
	"""Aendert die Version des geupgradeten Packages
	
	newVersion: neue Version des Packages
	packageName: Name des Packages
	"""
	global packeList
	for x in packageList:
		if x.name == packageName:
			x.version = newVersion["Version"]
	print("Upgrade wurde installiert")

def listener():
	"""
	Diese Funktion wird von einem Thread benutzt und behandelt die verschiedenen
	Befehle des Clients. Der Client kann nach Updates suchen, die Packete upgraden und die Verbindung beenden.
	
	Update : Die Information aller Packete wird in eine Liste von dictionarys gepackt
	Upgrade: -name : ueberprueft, ob der angegebene Name in der Liste der Updates vorhanden ist. Ist er es wird das packet in die 	
		         Upgrade_List ueberfuehrt
		 -all  : Uebernimmt alle Packages aus der Update-List in die Upgrade-Liste
	
	pack       : Dictionary zum speichern der Packete, um sie im Heartbeat an den Server zu schicken.
	updateList : Sobald ein Upgrade angefragt wird, wird das Package aus der updateListe entfernt und in die Upgrade-Liste 
		     verschoben
	connected  : Variable, die entscheidet, ob auf Eingaben des seers gewartet werden soll.
	hertbeat   : Variable bei der Abfrage zur Serverbeendung. Verbindung darf nur beendet werden, wenn der heartbeat besteht."""
	global pack, updateList, connected, heartbeat
	while connected:
		action = input()
		action = action.split(" ")
		if action[0] == "update":
			for x in range(0,len(packageList)):
				packageDict.update({"Package"+str(x+1) : {"Packagename" : packageList[x].name,
								"Version" : packageList[x].version,
								"URL" : packageList[x].url}})	
			pack = {"Packages" : packageDict}
		elif action[0] == "upgrade":
			if len(action) > 1:
				if action[1] == "all":
					if len(upgrade) == 0:
						for x in updateList:
							upgrade.append({"Package" : x})	
					updateList = []		
				else:
					for x in updateList:
						if x == action[1]:
							upgrade.append({"Package" : x})	
					if x in updateList:
						updateList.remove(x)
			else:
				print("Gebe die Datei oder all nach upgrade an")		
		elif action[0] == "end" and heartbeat:
			connected = False

def getTime():
	"""Gibt das Datum und die Uhrzeit zurueck"""
	return strftime("%Y-%m-%d %H:%M:%S", gmtime())

def getClientID():
	"""Gibt die MacAdresse zurück.
	Gegebenenfalls mit Zusatz zum Testen von 2 Adressen"""
	return str(getnode()) + "--Number1"

def getCPUInfo():
	"""Benutzt Unix-Befehle um Informationen ueber die CPU zu bekommen.Die Ausgabe des Befehls wird in einer Varibale gespeichert.
	Mittels Regular Expressions werden die gesuchten Daten herausgefiltert."""
	cpu = subprocess.Popen(["lscpu | grep -E Arc\|name\|CPU"], stdout=subprocess.PIPE, shell=True) 
	cpu1 = str(cpu.communicate()[0]).replace('\\n','\n')
	cpu1 = cpu1[2: len(cpu1)-2]

	cpu1 = cpu1.split('\n')

	cpuInfo = {}
	for x in range(0, len(cpu1)):
		pattern1 = re.compile(r"Architecture")
		m = pattern1.search(cpu1[x])
		if m:
			dictString = cpu1[x][m.span()[1]+1:]
			cpuInfo.update({m.group() : dictString.replace('  ','')})
			continue
		pattern2 = re.compile(r"Model name")
		m = pattern2.search(cpu1[x])
		if m:
			dictString = cpu1[x][m.span()[1]+1:]
			cpuInfo.update({m.group() : dictString.replace('  ','')})
			continue
		pattern3 = re.compile(r"CPU\(s\)")
		m = pattern3.match(cpu1[x])
		if m:
			dictString = cpu1[x][m.span()[1]+1:]
			cpuInfo.update({m.group() : dictString.replace('  ','')})
			continue
	return cpuInfo

def getRAMInfo():
	"""Benutzt Unix-Befehle um Informationen ueber den RAM zu bekommen.Die Ausgabe des Befehls wird in einer Varibale gespeichert.
	Mittels Regular Expressions werden die gesuchten Daten herausgefiltert."""
	ram = subprocess.Popen(["cat /proc/meminfo | grep -E Mem"], stdout=subprocess.PIPE, shell=True)
	ram1 = str(ram.communicate()[0]).replace('\\n','\n')
	ram1 = ram1[2: len(ram1)-2]
	ram1 = ram1.split('\n')

	ramPattern = re.compile(r":")

	ramInfo = {}
	for x in range(0, len(ram1)):
		m = ramPattern.search(ram1[x])
		dictName = ram1[x][0:m.span()[0]]
		dictInfo = (ram1[x][m.span()[1]:]).replace(' ','')
		ramInfo.update({dictName : dictInfo})
	return ramInfo

#deutsche und englische Beschreibung
def getGPUInfo():
	"""Benutzt Unix-Befehle um Informationen ueber die CPU zu bekommen.Die Ausgabe des Befehls wird in einer Varibale gespeichert.
	Mittels Regular Expressions werden die gesuchten Daten herausgefiltert."""
	gpu = subprocess.Popen(["lshw -c video | grep -E Besch\|desc\|Prod\|prod\|Herst\|vendor\|Takt\|clock"], stdout=subprocess.PIPE,stderr=subprocess.STDOUT, shell=True)

	gpu1 = str(gpu.communicate()[0]).replace('\\n','\n')

	gpu1 = gpu1[2: len(gpu1)-2]
	gpu1 = gpu1.split('\n')


	gpuPattern = re.compile(r":")
	warningPattern = re.compile(r"WARN")
	gpuInfo= {}
	for x in range(0, len(gpu1)):
		m2 = warningPattern.search(gpu1[x])
		if not m2:
			m = gpuPattern.search(gpu1[x])
			dictName = gpu1[x][0:m.span()[0]].replace('  ','')
			dictInfo = (gpu1[x][m.span()[1]:]).replace('  ','')
			gpuInfo.update({dictName : dictInfo})
	return gpuInfo

def getHardwareInfo():
	"""Erzeugt ein dict mit der Client-ID und der Information ueber CPU, RAM, GPU und gibt dieses zurueck."""
	info = {"Client-ID": getClientID(),
		"Info"     : {"CPU:Info" : getCPUInfo(),
			      "RAM-Info" : getRAMInfo(),
			      "GPU-Info" : getGPUInfo()
			     }
		}
	return info

def startConnection(s):
	"""Wartet auf den Server, bis er eine Nachricht schickt."""
	accept = False
	while not accept:
		recievedbytes = s.recv(50)
		if (len(recievedbytes) == 0):
			break;
		print(recievedbytes.decode('utf-8'))
		accept = True

def connectToNewPort(s):
	"""Sendet die Infos ueber die Hardware an den Server und wartet, bis der Server ihm einen neuen Port zuteilt. Schließt den Socket.
	s: der Socket. der Socket wird fuer das Senden und Empfangen von Daten uebergeben."""
	global newPort, port
	hardinfo = getHardwareInfo()
	infotext = json.dumps(hardinfo)
	s.send(bytes(infotext,'utf-8'))	
	recievedbytes = s.recv(50)
	newPort = recievedbytes.decode('utf-8')
	newPort = json.loads(newPort)
	port = newPort["newPort"]
	s.close()
	del(s)

def newConnection():
	"""Erstellt einen neuen Socket um sich mit dem neuen Port mit dem Server zu verbinden.
	Gibt den neu erstellten Socket s zurueck"""
	global port, connected
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	time.sleep(0.5)
	s.connect((host,port))
	time.sleep(0.5)
	connected = True
	return s

def communication(s):
	"""Wartet auf Nachrichten des Servers, bis er sagt, der Port wurde gewechselt und ihn anfordert neue Informationen zu schicken.Der 	
	Client sendet darauf alle seine Informationen.
	
	s : der Socket wird zum Senden und Empfangen von Daten uebergeben"""
	clientID = getClientID()
	recievedbytes = s.recv(50)
	message = recievedbytes.decode('utf-8')
	message = json.loads(message)
	print(message["info"])
	time.sleep(0.5)

	recievedbytes = s.recv(50)
	message = recievedbytes.decode('utf-8')
	message = json.loads(message)
	print(message["info2"])
	time.sleep(0.5)

	if message["info2"] == "Send Client Data":
		data = {"Hostname" : socket.gethostname(),
			"Client-ID": clientID,
			"IP"       : socket.gethostbyname(socket.gethostname()),	
			"Alive"    : "True",
			"Datum"    : getTime(),
			"Info"     : {"CPU-Info" : getCPUInfo(),
				      "RAM-Info" : getRAMInfo(),
				      "GPU-Info" : getGPUInfo()
				     }
			}
		data = json.dumps(data)
		s.send(bytes(data,'utf-8'))
	

def heartbeat(s):
	"""Sendet die Befehle und den heartbeat an den Server. An Update- oder Upgrade-Befehle wird der Heartbeat angefuegt. Somit kann dieser
	immer gesendet werden ohne durch andere Befehle auszufallen. Der Thread wird gestartet, um auf Eingaben in der Kommandozeile zu warten.
	Heartbeat: Die ID des Clients wird gesendet
	Update   : Sendet Information der installierten Packete an den Server. Bekommt als Antwort die Namen der Packete
	Upgrade  : Sendet das Packet an den Server. Ist das Packet zu groß, wird das Packet mehrmals gesendet
		   Es koennen auch mehrere Upgrades durchgefuehrt werden.
	
	connected : Wird im listener() die Variable connected auf False gesetzt, wird der heartbeat und die Verbindung zum Server beendet.
	heartbeat : Die Kommunikation kann nur beendet werden, wenn die heartbeatVariable True ist. Dadurch kannn es nicht zu vorzeitigem 
		    Beenden der Serverkommunikation durch User kommen.
	upgrade   : Liste Der Packages die upgegradet werden sollen.
	pack      : Liste der Packages. Wird an den Server gesendet, um nach Updates anzufragen.
	updateList: Hier werden die Packages mit vorhandenen upgrades eingefuegt."""
	global connected, heartbeat, upgrade, pack, updateList
	t = Thread(target = listener)
	t.start()	
	gettingUpgrade = False
	clientID = getClientID()
	while connected:
		heartbeat = True
		time.sleep(0.5)
		if pack is not None:
			pack.update({"Client-ID": clientID})
			pack =  json.dumps(pack)			
			s.send(bytes(pack, 'utf-8'))
			pack = None
			time.sleep(0.5)

			updater = s.recv(200)
			updater = updater.decode('utf-8')
			updater = json.loads(updater)
			updateList=[]
			if type(updater["Updates"]) == str:
				print(updater["Updates"])
			else:
				for x in range(0, len(updater["Updates"])):
					updateList.append(updater["Updates"]["update" + str(x+1)])
		
			if len(updateList) > 0:
				if len(updateList) == 1:
					print("Es ist ein Update verfügbar für: " + str(updateList[0]))
				else:
					print("Es sind Updates verfügbar für: ")
					for x in updateList:
						print("\t" + str(x))
				
		elif len(upgrade) > 0:
			data = ""
			for x in range(0, len(upgrade)):
				upgradePackage = {"Upgrade" : upgrade[x]}
				gettingUpgrade = True
				while gettingUpgrade:		
					upgradePackage.update({"Client-ID": clientID})
					upgradePackage = json.dumps(upgradePackage)
					s.send(bytes(upgradePackage,'utf-8'))
					time.sleep(0.5)
				
					upgradeText = s.recv(5000)
					upgradeText = upgradeText.decode('utf-8')
					upgradeText = json.loads(upgradeText, strict=False)
					if upgradeText["Upgrade"] == "start":
						data += upgradeText["data"]
						print("Upgrade wird installiert ...")
						if upgradeText["end"]:
							f = open(upgradeText["Filename"], "wb")
							f.write(bytes(data,'latin-1'))
							f.close()
							gettingUpgrade = False
						upgradePackage = {}
					if not gettingUpgrade:
						message = {"message":"upgraded","Name" : upgrade[x]["Package"]}
						message.update({"Client-ID": clientID})
						message = json.dumps(message)
						s.send(bytes(message,'utf-8'))
						time.sleep(0.5)
						version = s.recv(100)
						version = version.decode('utf-8')
						version = json.loads(version)
						versionThread = Thread(target=changeVersion, args=(version,upgrade[x]["Package"],))
						versionThread.start()	
			upgrade = []
		else:
			beatID = json.dumps({"Client-ID": clientID})
			s.send(bytes(beatID,'utf-8'))
	if not connected:
		heartbeat = False
		t.join()
		s.close()
		print("Verbindung wurde beendet.")


#zufaellige Testpackete werden geladen
package1 = Package("test1", "1.0.4", "http://localhost:9000/ressources/myclient_1.0.zip")
package2 = Package("useless_Package", "1.0.0", "http://localhost:9000/ressources/asd.zip")
package3 = Package("package1", "2.3.5", "http://localhost:9000/ressources/importantStuff.zip")
package4 = Package("lastPackage", "3.4.2", "http://localhost:9000/ressources/fancy.zip")

anzahlPackages = random.randint(0,3)

packageList=[]

if(anzahlPackages == 0):
	packageList.append(package2)
elif(anzahlPackages == 1):
	packageList.append(package4)
	packageList.append(package3)
elif(anzahlPackages == 2):
	packageList.append(package3)
	packageList.append(package1)
	packageList.append(package2)
else:
	packageList.append(package3)
	packageList.append(package4)
	packageList.append(package1)
	packageList.append(package2)

host = 'localhost'
port = 9000

#connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.connect((host,port))

startConnection(s)
connectToNewPort(s)
s = newConnection()
communication(s)
heartbeat(s)
