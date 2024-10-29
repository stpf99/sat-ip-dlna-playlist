# getchannels.py
import sys

server = sys.argv[1]
inputFilename = sys.argv[2]
outputFilename = sys.argv[2].replace("php", "xml")
source = sys.argv[3]

newTransponder = 0
newChannel = 0
newRadioChannel = 0
apidArray = []
opidArray = []
channelname = ""
frequency = ""
polarity = ""
delsys = ""
modulation = ""
symrate = ""

def generate_pids(vpid, apids, opids):
    pids = []

    if vpid:
        pids.append(vpid)

    pids.extend(apids)
    pids.extend(opids)

    pids = [pid for pid in pids if pid]
    while len(pids) < 6:
        if vpid:
            pids.append(vpid)
        elif apids:
            pids.append(apids[0])
        elif opids:
            pids.append(opids[0])
        else:
            pids.append('0')

    return ','.join(pids[:6])

with open(inputFilename, "r") as f, open(outputFilename, "w") as o:
    for line in f:
        if(newRadioChannel > 0):
            if(newRadioChannel < 2):
                newRadioChannel = newRadioChannel + 1
                continue
            elif(newRadioChannel == 2):
                channelname, ignore1 = line.lstrip().split('<', 1)
                newRadioChannel = newRadioChannel + 1
            elif(newRadioChannel < 9):
                newRadioChannel = newRadioChannel + 1
                continue
            elif(newRadioChannel == 9):
                ignore1, apid = line.split('>', 1)
                apid = apid.split('<', 1)[0]
                apid = apid.split('&', 1)[0]
                apid = apid.split(" ", 1)[0]
                apidArray.append(apid)
                newRadioChannel = newRadioChannel + 1
            else:
                if("pid\">" in line):
                    if "apid" in line.lower():
                        ignore1, apid = line.split('>', 1)
                        apid = apid.split('<', 1)[0]
                        apid = apid.split('&', 1)[0]
                        apid = apid.split(" ", 1)[0]
                        apidArray.append(apid)
                    else:
                        ignore1, opid = line.split('>', 1)
                        opid = opid.split('<', 1)[0]
                        opid = opid.split('&', 1)[0]
                        opid = opid.split(" ", 1)[0]
                        opidArray.append(opid)
                    newRadioChannel = newRadioChannel + 1
                    continue
                else:
                    pids = generate_pids('', apidArray, opidArray)
                    url = f'<channel number="NR"><tuneType>DVB-S-AUTO</tuneType><visible>true</visible><type>radio</type><name>{channelname}</name><freq>{frequency}</freq><pol>{polarity}</pol><sr>{symrate}</sr><src>{source}</src><pids>{pids}</pids></channel>'
                    o.write(url + "\n")
                    newRadioChannel = 0
                    apidArray = []
                    opidArray = []
                    continue
        elif(newChannel > 0):
            if(newChannel < 6):
                newChannel = newChannel + 1
                continue
            elif(newChannel == 6):
                ignore1, vpid = line.split('>', 1)
                vpid, ignore1 = vpid.split('<', 1)
                vpid = vpid.split(" ", 1)[0]
                newChannel = newChannel + 1
                continue
            elif(newChannel == 7):
                ignore1, apid = line.split('>', 1)
                apid = apid.split('<', 1)[0]
                apid = apid.split('&', 1)[0]
                apid = apid.split(" ", 1)[0]
                apidArray.append(apid)
                newChannel = newChannel + 1
                continue
            else:
                if("pid\">" in line):
                    if "apid" in line.lower():
                        ignore1, apid = line.split('>', 1)
                        apid = apid.split('<', 1)[0]
                        apid = apid.split('&', 1)[0]
                        apid = apid.split(" ", 1)[0]
                        apidArray.append(apid)
                    else:
                        ignore1, opid = line.split('>', 1)
                        opid = opid.split('<', 1)[0]
                        opid = opid.split('&', 1)[0]
                        opid = opid.split(" ", 1)[0]
                        opidArray.append(opid)
                    newChannel = newChannel + 1
                    continue
                else:
                    pids = generate_pids(vpid, apidArray, opidArray)
                    url = f'<channel number="NR"><tuneType>DVB-S-AUTO</tuneType><visible>true</visible><type>tv</type><name>{channelname}</name><freq>{frequency}</freq><pol>{polarity}</pol><sr>{symrate}</sr><src>{source}</src><pids>{pids}</pids></channel>'
                    o.write(url + "\n")
                    newChannel = 0
                    apidArray = []
                    opidArray = []
                    continue
        elif(newTransponder == 0):
            if("<table class=\"frq\">" in line):
                newTransponder = 1
                continue
            if(" title=\"Id:" in line):
                ignore1, rest = line.split(':', 1)
                channelname, rest = rest.lstrip().split('"', 1)
                newChannel = 1
            if("<img src=\"/radio.gif\"" in line):
                newRadioChannel = 1
        elif(newTransponder == 1):
            if("class=\"bld\">" in line):
                newTransponder = 2
                continue
        elif(newTransponder == 2):
            if("class=\"bld\">" in line):
                ignore1, rest = line.split('>', 1)
                frequency, rest = rest.split('<', 1)
                frequency, ignore1 = frequency.split('.', 1)
                ignore1, ignore2, rest = rest.split('>', 2)
                polarity, rest = rest.split('<', 1)
                ignore1, ignore2, ignore3, ignore4, ignore5, ignore6, ignore7, ignore8, ignore9, rest = rest.split('<', 9)
                ignore1, rest = rest.split('>', 1)
                delsys, rest = rest.split('<', 1)
                delsys = delsys.replace('-', '')
                ignore1, ignore2, rest = rest.split('>', 2)
                modulation, rest = rest.split('<', 1)
                ignore1, ignore2, ignore3, rest = rest.split('>', 3)
                symrate, rest = rest.split('<', 1)
                newTransponder = 0

f.close()
o.close()
