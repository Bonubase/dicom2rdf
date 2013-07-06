#!/usr/bin/python

import sys
import dicom,rdflib
sys.path.append('..')
import uritools
from sopclasses import *
from namespaces import *

graph=uritools.newgraph()

for uid,value in dicom._UID_dict.UID_dictionary.items():
    name=value[0]
    if not uid or not name:
        continue
    uid=uid.strip()
    subject=uritools.urifromuid(uid)
    graph.add((subject,RDFS.label,rdflib.Literal(name)))
    if uid in sopclasses:
        graph.add((subject,RDF.type,OWL.Class))

graph=graph.serialize(sys.stdout,format="pretty-xml")
