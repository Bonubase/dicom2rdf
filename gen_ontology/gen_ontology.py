#!/usr/bin/python

import sys,random,time,datetime
import dicom,rdflib,rdflib.collection
sys.path.append('..')
import uritools,settings
from datadict import *
from valid_ies import *
from iesbyattribute import *
from sequencesbyattribute import *
from sopclasses import *
from namespaces import *

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

# removes unused blank node ids in RDF/XML (rdflib cannot do this)
def removeunusedblanknodeids(s):
    pos=s.find(' rdf:nodeID="')
    while pos>0:
        pos+=13
        pos1=s.find('"',pos)
        assert pos1 > pos
        nodeid=s[pos:pos1]
        s1=s.replace(' rdf:nodeID="'+nodeid+'"','',1)
        if nodeid not in s1:
            s=s1
            pos-=13
        pos=s.find(' rdf:nodeID="',pos)
    return s

graph=uritools.newgraph()

for tag,(vr,vm,label,restricted,name) in datadict.items():
  if not name:
      continue
  if vr=='NONE':
      continue
  assert label
  s1=uritools.urifromtag(tag)
  s2=uritools.urifromtag(tag,numeric=True)

  for subject,subject1 in [(s1,s2),(s2,s1)]:

    graph.add((subject,OWL.equivalentProperty,subject1))

    graph.add((subject,RDFS.isDefinedBy,settings.ontodoc))
    graph.add((subject,RDFS.label,rdflib.Literal(label)))    

    range=None
    if vr=='SQ' or vm!='1':
        cl=OWL.ObjectProperty
        range=CO.List
    elif vr in ('UI','OB','OW','OB or OW','OW or OB'):
        cl=OWL.ObjectProperty
    else:
        cl=OWL.DatatypeProperty
        if vr in ('AE','CS','LO','LT','SH','ST','UT','PN'):
            range=RDFS.Literal
        elif vr in ('IS','SL','SS','UL','AT','US','US or SS'):
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
            assert False,vr

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
            union=rdflib.BNode()
            graph.add((subject,RDFS.domain,union))
            graph.add((union,RDF.type,OWL.Class))
            graph.add((union,OWL.unionOf,colbnode))

  if vr=='SQ':
      s1=uritools.urifromtag(tag,isclass=True)
      s2=uritools.urifromtag(tag,isclass=True,numeric=True)
      for subject,subject1 in [(s1,s2),(s2,s1)]:
          graph.add((subject,RDF.type,OWL.Class))
          graph.add((subject,OWL.equivalentClass,subject1))
          graph.add((subject,RDFS.isDefinedBy,settings.ontodoc))
          graph.add((subject,RDFS.label,rdflib.Literal('Item of: '+label)))

for ie in valid_ies:
    subject=uritools.getieclass(ie)
    graph.add((subject,RDFS.isDefinedBy,settings.ontodoc))
    graph.add((subject,RDFS.label,rdflib.Literal(ie)))
    graph.add((subject,RDF.type,OWL.Class))

graph.add((CO.List,RDF.type,OWL.Class))

graph=graph.serialize(format="pretty-xml")

assert '<rdf:rest' not in graph # Sometimes rdflib fucks up. Just try again

graph=removeunusedblanknodeids(graph)
assert 'rdf:nodeID' not in graph

# basic information that needs to be on top
graph1=uritools.newgraph()
graph1.bind('vann',VANN)

graph1.add((settings.ontodoc,RDF.type,OWL.Ontology))
graph1.add((settings.ontodoc,VANN.preferredNamespacePrefix,rdflib.Literal(settings.ontoprefix)))
graph1.add((settings.ontodoc,VANN.preferredNamespaceUri,rdflib.Literal(settings.ontons)))
graph1.add((settings.ontodoc,DCTERMS.issued,rdflib.Literal(datetime.date(2013,4,29))))
today=rdflib.Literal(datetime.datetime.date(datetime.datetime.now()))
graph1.add((settings.ontodoc,DCTERMS.modified,today))

label='Healthcare metadata / DICOM ontology'
graph1.add((settings.ontodoc,RDFS.label,rdflib.Literal(label)))
graph1.add((settings.ontodoc,DCTERMS.title,rdflib.Literal(label)))
comment="""
Ontology for healthcare metadata - especially metadata found in DICOM files 
(Digital Imaging and Communications in Medicine, see http://dicom.nema.org/).

Author: Michael Brunnbauer, Bonubase GmbH (www.bonubase.com).
The author's email address is brunni@netestate.de.

See http://purl.org/healthcarevocab/v1help for explanations.
"""
graph1.add((settings.ontodoc,RDFS.comment,rdflib.Literal(comment)))
graph1.add((settings.ontodoc,DCTERMS.description,rdflib.Literal(comment)))

graph1.add((VANN.preferredNamespacePrefix,RDF.type,OWL.AnnotationProperty))
graph1.add((VANN.preferredNamespaceUri,RDF.type,OWL.AnnotationProperty))
graph1.add((DCTERMS.issued,RDF.type,OWL.AnnotationProperty))
graph1.add((DCTERMS.modified,RDF.type,OWL.AnnotationProperty))
graph1.add((DCTERMS.title,RDF.type,OWL.AnnotationProperty))
graph1.add((DCTERMS.description,RDF.type,OWL.AnnotationProperty))

graph1=graph1.serialize(format="pretty-xml")

# combine both graph serializations with graph1 on top
gh,gb,gf=rdfxmlsplit(graph)
g1h,g1b,g1f=rdfxmlsplit(graph1)
assert len(gh.split('\n'))==len(g1h.split('\n'))-2,gh+g1h
assert gf==g1f
print g1h+g1b+gb+gf
