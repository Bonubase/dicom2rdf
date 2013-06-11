#!/usr/bin/python

import sys,random,time,datetime
import dicom,rdflib,rdflib.collection
sys.path.append('..')
import uritools,settings
from valid_ies import *
from iesbyattribute import *
from sequencesbyattribute import *
from sopclasses import *

# namespaces
from rdflib.namespace import XSD
from rdflib.namespace import RDF
from rdflib.namespace import RDFS
from rdflib.namespace import OWL
DCTERMS=rdflib.namespace.Namespace('http://purl.org/dc/terms/')

# splits RDF/XML into header (<?xml?><rdf:RDF>), body and footer (</rdf:RDF>)
# needed because we cannot influence the order of serialization in rdflib
def rdfxmlsplit(s):
    header=''
    body=None
    footer=None
    for line in s.split('\n'):
        if body is None:
            line1=line.lstrip()
            if line1.startswith('<') and not line1.startswith('<?xml') and not line1.startswith('<rdf:RDF'):
                body=line+'\n'
            else:
                header+=line+'\n'
        elif footer is None:
            if '</rdf:RDF>' in line:
                footer=line+'\n'
            else:
                body+=line+'\n'            
        else:
            assert not line
    return header,body,footer

graph=uritools.newgraph()

for tag,value in dicom._dicom_dict.DicomDictionary.items():
    name=value[4]
    if not name:
        continue
    subject=uritools.urifromtag(tag)

    subject1=uritools.urifromtag(tag,numeric=True)
    graph.add((subject,OWL.sameAs,subject1))

    label=value[2]
    assert label
    graph.add((subject,RDFS.isDefinedBy,settings.ontodoc))
    graph.add((subject,RDFS.label,rdflib.Literal(label)))    

    vr=value[0]
    vm=value[1]
    range=None
    if vr=='SQ' or vm!='1':
        cl=OWL.ObjectProperty
        range=RDF.List
    elif vr=='UI':
        cl=OWL.ObjectProperty
    else:
        cl=OWL.DatatypeProperty
        if vr in ('AE','CS','LO','LT','SH','ST','UT','PN'):
            range=RDFS.Literal
        elif vr in ('IS','SL','SS','UL','US','US or SS'):
            range=XSD.long
        elif vr in ('DS','FL','OF','FD'):
            range=XSD.double
        elif vr=='AS':
            range=XSD.duration
        elif vr=='DA':
            range=XSD.date
        elif vr=='TM':
            range=XSD.time
        elif vr=='DT':
            range=XSD.dateTime
        else:
            cl=RDF.Property

    graph.add((subject,RDF.type,cl))
    if range is not None:
        graph.add((subject,RDFS.range,range))

    if tag in iesbyattribute or tag in sequencesbyattribute:
        ies=iesbyattribute.get(tag,{})
        ies=ies.get(None,[])
        sqs=sequencesbyattribute.get(tag,[])
        if len(ies+sqs)==1:
            for ie in ies:
                domain=uritools.getieclass(ie)
            for sq in sqs:
                domain=uritools.urifromtag(sq,isclass=True)
            graph.add((subject,RDFS.domain,domain))
        else:
            colitems=[]
            for ie in ies:
                colitems.append(uritools.getieclass(ie))
            for sq in sqs:
                colitems.append(uritools.urifromtag(sq,isclass=True))
            colbnode=rdflib.BNode()
            col=rdflib.collection.Collection(graph,colbnode,colitems)
            unionbnode=rdflib.BNode()
            graph.add((subject,RDFS.domain,unionbnode))
            graph.add((unionbnode,RDF.type,OWL.Class))
            graph.add((unionbnode,OWL.unionOf,colbnode))

    if vr=='SQ':
        subject=uritools.urifromtag(tag,isclass=True)
        subject1=uritools.urifromtag(tag,isclass=True,numeric=True)
        graph.add((subject,OWL.sameAs,subject1))
        graph.add((subject,RDFS.isDefinedBy,settings.ontodoc))
        graph.add((subject,RDFS.label,rdflib.Literal('Item of: '+label)))
        graph.add((subject,RDF.type,OWL.Class))

for ie in valid_ies:
    subject=uritools.getieclass(ie)
    graph.add((subject,RDFS.isDefinedBy,settings.ontodoc))
    graph.add((subject,RDFS.label,rdflib.Literal(ie)))
    graph.add((subject,RDF.type,OWL.Class))

graph=graph.serialize(format="pretty-xml")

assert '<rdf:rest' not in graph

# basic information that needs to be on top
graph1=uritools.newgraph()
graph1.add((settings.ontodoc,RDF.type,OWL.Ontology))
label='Healthcare metadata / DICOM ontology'
graph1.add((settings.ontodoc,RDFS.label,rdflib.Literal(label)))
comment="""
Ontology for healthcare metadata - especially metadata found in DICOM files 
(Digital Imaging and Communications in Medicine, see http://dicom.nema.org/).

Author: Michael Brunnbauer, Bonubase GmbH (www.bonubase.com).
The author's email address is brunni@netestate.de.

See http://purl.org/healthcarevocab/v1help for explanations.
"""
graph1.add((settings.ontodoc,RDFS.comment,rdflib.Literal(comment)))
graph1.add((settings.ontodoc,DCTERMS.creator,settings.ontocreator))
graph1=graph1.serialize(format="pretty-xml")

# combine both graph serializations with graph1 on top
gh,gb,gf=rdfxmlsplit(graph)
g1h,g1b,g1f=rdfxmlsplit(graph1)
assert len(gh.split('\n'))==len(g1h.split('\n'))-1,gh+g1h
assert gf==g1f
print g1h+g1b+gb+gf
