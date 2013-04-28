#!/usr/bin/python

import sys
from parse import gettables,currentchapter,gettag,ischapter
sys.path.append('..')
from modulemacros import *
from iods import *

fixes=[
(' - For Presentation',''),
(' - For Processing',''),
('Computed Radiography','CR'),
('Secondary Capture','SC'),
('Optical Coherence Tomography','OCT'),
(' XRF',' X-RAY RF'),
('X-Ray Radiofluoroscopic','XRF'),
('Positron Emission Tomography','PET'),
]

def normalize(line):
    line=line.lstrip()
    while '   ' in line:
        line=line.replace('   ','  ')
    return line.split('  ')

def getclasses(lines):
    i=0
    classes=[]
    while i<len(lines):
        line=lines[i]
        i+=1
        parts=normalize(line)
        if len(parts)<2 or not parts[1].startswith('1.2.840.10008'):
            continue
        name=parts[0]
        namepos=line.find(name)
        uid=parts[1]
        uidpos=line.find(uid)
        iod=''
        if len(parts)>2:
            iod=parts[2]
            iodpos=line.find(iod,uidpos)

        line1=lines[i]
        parts1=normalize(line1)
        while len(parts1)<2 or not parts1[1].startswith('1.2.840.10008'):
            name1=None
            iod1=None
            if len(line1)>namepos and line1[namepos]!=' ':
                name1=line1[namepos:].split('  ')[0]
                name+=' '+name1
            if iod and len(line1)>iodpos and line1[iodpos]!=' ':
                iod1=line1[iodpos:]
                iod+=' '+iod1
            if name1 is None and iod1 is None:
                break
            i+=1
            line1=lines[i]
            parts1=normalize(line1)
        classes.append((uid,name,iod))
    return classes

print "sopclasses={"

f=open('sopclasses.txt',"r")
text=f.read()
f.close()
text=text.replace('\xad','-')

for uid,name,iod in getclasses(text.split('\n')):
    iodid=None
    iod1=''
    if iod.endswith(' Waveform'):
        iod1=iod[:-9]
    for s in [iod,name,iod1]:
        s=s.split('(')[0].strip()
        if not s:
            continue
        s=s.upper()
        for search,replace in fixes:
            search=search.upper()
            if search in s:
                s=s.replace(search,replace)
        if s.endswith(' STORAGE'):
            s=s[:-8]
        if not s.endswith(' IOD'):
            s+=' IOD'
        if s in iods:
            iodid=s
            break
    if iodid:
        print repr(uid)+': '+repr(iodid)+','
    else:
        print '# not found: '+uid
        print '# '+name
        if iod:
            print '# '+iod

print "}"
