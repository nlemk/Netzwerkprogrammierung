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

"""Bool'scher Wert, ob die Verbindung steht"""
connected = False
"""Ein dict fuer die Packages. Wird fuer die Update-frage benutzt"""
pack = None
"""Wert, ob der Heartbeat noch gesendet wird."""
heartbeat = False
"""Ein dict in dem ein Package, mit seinen Daten gespeichert ist"""
packageDict ={}
"""Liste mit Namen der Packages, fuer die ein Update verfuegbar ist"""
updateList = []
"""Liste von dicts mit Namen der Packete, die upgegraded werden sollen"""
upgrade = []


def changeVersion(newVersion, packageName):
	"""Aendert die Version des geupgradetem Packages
	
	newVersion: neue Version des Packages
	packageName: Name des Packages
	"""
	global packeList
	for x in packageList:
		if x.name == packageName:
			x.version = newVersion["Version"]
	print("version changed")

def listener():
	"""
	Diese Funktion wird von einem Thread benutzt und behandelt die verschiedenen
	Befehle des Clients. Der Client kann nach Updates suchen, die Packete upgraden und die Verbindung beenden.			
	"""
	global pack, updateList, connected, heartbeat
	while connected:
		action = input()
		action = action.split(" ")
		#print(input)
		if action[0] == "update":
			print("update")
			for x in range(0,len(packageList)):
				packageDict.update({"Package"+str(x+1) : {"Packagename" : packageList[x].name,
								"Version" : packageList[x].version,
								"URL" : packageList[x].url}})	
		
			pack = {"Packages" : packageDict}
			#pack =  json.dumps(pack)
			print(len(pack))
			#s.send(bytes(pack, 'utf-8'))
			print("erfolgreich")
			print(pack)
		elif action[0] == "upgrade":
			print("upgrade")
			if len(action) > 1:
				print(action[1])
				if action[1] == "all":
					if len(upgrade) == 0:
						for x in updateList:
							upgrade.append({"Package" : x})	
					updateList = []		
				else:
					for x in updateList:
						if x == action[1]:
							upgrade.append({"Package" : x})	
					updateList.remove(x)
			else:
				print("Gebe die Datei odet all nach upgrade an")		
		elif action[0] == "end" and heartbeat:
			connected = False

def getTime():
	"""Gibt das Datum und die Uhrzeit zurueck"""
	return strftime("%Y-%m-%d %H:%M:%S", gmtime())

def getClientID():
	"""Gibt die MacAdresse zurück.
	Gegebenenfalls mit Zusatz zum Testen von 2 Adressen"""
	return str(getnode()) + "--Number1"

dateTime = getTime()
print(dateTime)

clientID = getClientID()

package1 = Package("test1", "1.0.4", "http://localhost:9000/ressources/myclient_1.0.zip")
package2 = Package("useless Package", "1.0.0", "http://localhost:9000/ressources/nothing.zip")
package3 = Package("package1", "2.3.5", "http://localhost:9000/ressources/importantStuff.zip")
package4 = Package("lastPackage", "3.4.2", "http://localhost:9000/ressources/fancy.zip")

#4Packages momentan
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


#print(len(packageList))
#packageDict = {3:{4:5,6:3}}
#packageDict[3].update({2:9})
#packageDict[3].update({4:6})
#print(packageDict)
	
'''system = platform

systemInfo = {"system" : system.system(),
	      "machine" : system.machine(),
	      "version" : system.version(),
	      "platform" : system.platform(),
	      "processor" : system.processor()
		}'''

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

hardinfo = getHardwareInfo()
infotext = json.dumps(hardinfo)
#json.loads(infotext)

beatID = json.dumps({"Client-ID": clientID})
#json.loads(beatID)

host = 'localhost'
port = 9000
connectionRefused = True
#connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.connect((host,port))

def startConnection(s):
	"""Wartet auf den Server."""
	print("startConnection")
	accept = False
	while not accept:
		recievedbytes = s.recv(50)
		if (len(recievedbytes) == 0):
			break;
		print(recievedbytes.decode('utf-8'))
		accept = True

def connectToNewPort(s):
	"""Sendet die Infos ueber die Hardware an den Server und wartet, bis der Server ihm einen neuen Port zuteilt. Schließt den Socket"""
	global infotext,newPort, port
	print("connectToNewPort")
	print(infotext)
	s.send(bytes(infotext,'utf-8'))	
	print("newPort")
	recievedbytes = s.recv(50)
	newPort = recievedbytes.decode('utf-8')
	newPort = json.loads(newPort)
	print(newPort)
	port = newPort["newPort"]
	s.close()
	del(s)

def newConnection():
	"""Erstellt einen neuen Socket um sich mit dem neuen Port mit dem Server zu verbinden"""
	print("newConnection")
	global port, connected
	print("newPort")
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	print(port)
	time.sleep(0.5)
	s.connect((host,port))
	time.sleep(0.5)
	connected = True
	return s

def communication(s):
	"""Wartet auf Nachrichten des Servers.sind die Nachrichten engekommen, darf der Client all seine Informationen senden."""
	global connected, heartbeat, dateTime, clientID
	recievedbytes = s.recv(50)
	message = recievedbytes.decode('utf-8')
	message = json.loads(message)
	print(message["info"])
	time.sleep(0.5)

	recievedbytes = s.recv(50)
	message = recievedbytes.decode('utf-8')
	message = json.loads(message)
	print(message)
	time.sleep(0.5)

	if message["info2"] == "Send Client Data":
		print("send")
		data = {"Hostname" : socket.gethostname(),
			"Client-ID": clientID,
			"IP"       : socket.gethostbyname(socket.gethostname()),	
			"Alive"    : "True",
			"Datum"    : dateTime,
			"Info"     : {"CPU-Info" : getCPUInfo(),
				      "RAM-Info" : getRAMInfo(),
				      "GPU-Info" : getGPUInfo()
				     }
			}
		data = json.dumps(data)
		s.send(bytes(data,'utf-8'))
	

def heartbeat(s):
	"""Sendet die Befehle und den heartbeat an den Server. An Update- oder Upgrade-Befehle wird der heartbeat angefuegt. Somit kann dieser
	immergesendet werden ohne durch andere Befehle auszufallen. Der Thread wird gestartet um auf Eingaben in der Kommandozeile zu warten.
	Heartbeat: Die ID des Clients wird gesendet
	Update   : Sendet Information der installierten Packete an den Server. Bekommt als Antwort die Namen der Packete
	Upgrade  : Sendet das Packet an den Server. Ist das Packet zu groß, wird das Packet mehrmals gesendet"""
	global connected, heartbeat, dateTime, clientID, upgrade, pack, updateList
	t = Thread(target = listener)
	t.start()	
	gettingUpgrade = False
	while connected:
		heartbeat = True
		time.sleep(0.5)
		if pack is not None:
			pack.update({"Client-ID": clientID})
			pack =  json.dumps(pack)
			s.send(bytes(pack, 'utf-8'))
			#print(pack)
			pack = None
			time.sleep(0.5)

			updater = s.recv(200)
			updater = updater.decode('utf-8')
			updater = json.loads(updater)
			print(updater)
			updateList=[]
			if type(updater["Updates"]) == str:
				print(updater["Updates"])
			else :
				for x in range(0, len(updater["Updates"])):
					updateList.append(updater["Updates"]["update" + str(x+1)])
		
			if len(updateList) > 0:
				print(updateList)
				
		elif len(upgrade) > 0:
			#todo upgrade
			data = ""
			for x in range(0, len(upgrade)):
				print(x)
				upgradePackage = {"Upgrade" : upgrade[x]}
				gettingUpgrade = True
				while gettingUpgrade:	
					print("get upgrade")	
					upgradePackage.update({"Client-ID": clientID})
					upgradePackage = json.dumps(upgradePackage)
					print(upgradePackage)
					s.send(bytes(upgradePackage,'utf-8'))
					time.sleep(0.5)
				
					upgradeText = s.recv(5000)
					upgradeText = upgradeText.decode('utf-8')
					#upgradeText = json.loads(upgradeText)
					upgradeText = json.loads(upgradeText, strict=False)
					print(upgradeText["data"])
					if upgradeText["Upgrade"] == "start":
						data += upgradeText["data"]
						print(upgradeText["end"])
						if upgradeText["end"]:
							f = open(upgradeText["Filename"], "wb")
							f.write(bytes(data,'latin-1'))
							f.close()
							print("----------------------")
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
			s.send(bytes(beatID,'utf-8'))
	if not connected:
		heartbeat = False
		t.join()
		s.close()


startConnection(s)
connectToNewPort(s)
s = newConnection()
communication(s)
heartbeat(s)
