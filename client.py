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

dateTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
print(dateTime)

clientID = str(getnode()) + "--Number1"

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
	"CPU:Info" : cpuInfo,
        "RAM-Info" : ramInfo,
	"GPU-Info" : gpuInfo
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
time.sleep(0.1)
s.connect((host,port))


while True:
	time.sleep(0.5)
	s.send(bytes(beatID,'utf-8'))

s.close()
