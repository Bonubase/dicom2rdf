#!/usr/bin/python

import sys
sys.path.append('..')
from parse import hextag
from expandmacro import expand

from datadict import *
from modulemacros import *

# check for infinite recursions
for mm in modulemacros:
    expand(mm)

def addtosba(tag,element):
    if element in sequencesbyattribute:
        if tag not in sequencesbyattribute[element]:
            sequencesbyattribute[element].append(tag)
    else:
        sequencesbyattribute[element]=[tag]

def addsequence(element):
    tag,elements=element
    tag=hextag(tag)
    for element in elements:
        if type(element)==long:
            addtosba(tag,element)
        elif type(element)==str:
            if element==mm:
                print >> sys.stderr, "macro",mm,"includes itself"
                continue
            for element in expand(element):
                addtosba(tag,element)
        else:
            addtosba(tag,element[0])
            addsequence(element)

sequencesbyattribute={}

for chapter,table,elements in modulemacros.values():
    for element in elements:
        if type(element) in (long,str):
            continue
        addsequence(element)

print "# list of possible sequences an attribute can occur within by attribute"
print "sequencesbyattribute={"

for tag,sqlist in sequencesbyattribute.items():
    reprlist='['
    for item in sqlist:
        reprlist+=item+', '
    reprlist=reprlist[:-2]+']'

    print '# '+keyword_for_tag(tag)
    print hextag(tag)+': ',reprlist+','

print "}"
