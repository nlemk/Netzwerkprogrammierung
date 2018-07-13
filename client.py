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

conn = True
pack = None
packageDict ={}
def listener():
	global pack
	while conn:
		
		action = input()
		print(action)
		if action == "update":
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
		elif action == "upgrade":
			x = 1
			#upgrade


dateTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
print(dateTime)

clientID = str(getnode()) + "--Number1"

package1 = Package("test1", "1.0.8", "http://localhost:9000/resources/myclient_1.0.tgz")
package2 = Package("useless Package", "1.0.0", "http://localhost:9000/resources/nothing.tgz")
package3 = Package("package1", "2.7.5", "http://localhost:9000/resources/importantStuff.tgz")
package4 = Package("lastPackage", "3.5.1", "http://localhost:9000/resources/fancy.tgz")

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

DEVNULL = open(os.devnull, 'wb')
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


#deutsche und englische Beschreibung
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
		m = ramPattern.search(gpu1[x])
		dictName = gpu1[x][0:m.span()[0]].replace('  ','')
		dictInfo = (gpu1[x][m.span()[1]:]).replace('  ','')
		gpuInfo.update({dictName : dictInfo})

info = {"Client-ID": clientID,
	"Info"     : {"CPU:Info" : cpuInfo,
        	      "RAM-Info" : ramInfo,
		      "GPU-Info" : gpuInfo
	             }
	}

infotext = json.dumps(info)
#json.loads(infotext)

beatID = json.dumps({"Client-ID": clientID})
#json.loads(beatID)

host = 'localhost'
port = 9000
connectionRefused = True

#connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
s.connect((host,port))


accept = False
while not accept:
	recievedbytes = s.recv(50)
	if (len(recievedbytes) == 0):
		break;
	print(recievedbytes.decode('utf-8'))
	accept = True

s.send(bytes(infotext,'utf-8'))	
print("newPort")
recievedbytes = s.recv(50)
newPort = recievedbytes.decode('utf-8')
newPort = json.loads(newPort)
port = newPort["newPort"]
s.close()
del(s)

#newSocket
print("newPort")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
print(port)
time.sleep(0.5)
s.connect((host,port))
time.sleep(0.5)

recievedbytes = s.recv(50)
message = recievedbytes.decode('utf-8')
print(message)
message = json.loads(message)
print(message["info"])
time.sleep(0.5)

recievedbytes = s.recv(50)
message = recievedbytes.decode('utf-8')
print(message)
time.sleep(0.5)

if message == "Send Client Data":
	print("send")
	data = {"Hostname" : socket.gethostname(),
		"Client-ID": clientID,
		"IP"       : socket.gethostbyname(socket.gethostname()),	
		"Alive"    : "True",
		"Datum"    : dateTime,
		"Info"     : {"CPU-Info" : cpuInfo,
        		      "RAM-Info" : ramInfo,
			      "GPU-Info" : gpuInfo
			     }
		}
	data = json.dumps(data)
	s.send(bytes(data,'utf-8'))
	
count = 0
t = Thread(target = listener)
t.start()
while True:
	time.sleep(0.5)
	count += 1
	if pack is not None:
		pack.update({"Client-ID": clientID})
		pack =  json.dumps(pack)
		s.send(bytes(pack, 'utf-8'))
		#print(pack)
		pack = None
		time.sleep(0.5)

		updateList = []
		updater = s.recv(200)
		updater = updater.decode('utf-8')
		updater = json.loads(updater)
		print(updater)
		if type(updater["Updates"]) == str:
			print(updater["Updates"])
		else :
			for x in range(0, len(updater["Updates"])):
				updateList.append(updater["Updates"]["update" + str(x+1)])
		
		if len(updateList) > 0:
			print(updateList)
				
	else:
		s.send(bytes(beatID,'utf-8'))

s.close()
