#!/usr/bin/python

import sys,random,time,datetime
import dicom,rdflib
import uritools,settings

from sopclasses import *
from iods import *
from iesbyattribute import *
from sequencesbyattribute import *

# namespaces
from rdflib.namespace import XSD
from rdflib.namespace import RDF
from rdflib.namespace import RDFS
DCTERMS=rdflib.namespace.Namespace('http://purl.org/dc/terms/')
FOAF=rdflib.namespace.Namespace('http://xmlns.com/foaf/0.1/')

# global variables for generating unique URIs
starttime=time.time()
individualindex=1

# remove invalid XML characters
def cleantext(text):
    assert type(text)==unicode
    rueck=u''
    for c in text:
        o=ord(c)
        # control characters
        if o < 32:
            # why does pydicom not remove this ? 
            if o==0:
                pass
            # CR and LF are valid in DICOM and XML
            elif o in (13,10):
                rueck+=c
            # FF is valid in DICOM but not in XML
            elif o==12:
                rueck+='\r\n\r\n'
            # ESC is valid in DICOM but not in XML
            elif o==27:
                rueck+=u'\ufffd' # unicode replacement character
            else:
                assert False,o
        # other invalid XML characters (valid in DICOM?)
        elif o==0xfffe or o==0xffff or ( 0xd800 <= o <= 0xdfff ):
            rueck+=u'\ufffd' # unicode replacement character
        else:
            rueck+=c
    return rueck

# timezone class to generate datetime objects with timezone info
class tz(datetime.tzinfo):
    def __init__(self,offset,sign):
        assert len(offset)==4
        hours=int(offset[:2])
        minutes=int(offset[2:])
        self.offset=datetime.timedelta(hours=hours,minutes=minutes)
        self.offset*=sign

    def utcoffset(self, dt):
        return self.offset

    def tzname(self, dt):
        return None

    def dst(self, dt):
        return None

# parses a DICOM date (VR DA)
def parsedate(value):
    assert len(value)==8
    year=int(value[:4])
    month=int(value[4:6])
    day=int(value[6:])
    return datetime.date(year,month,day)

# parses a DICOM time (VR TM)
def parsetime(value):
    assert len(value)>=2
    hour=int(value[:2])
    minute=0
    second=0
    microsecond=0
    if len(value)>2:
        minute=int(value[2:4])
    if len(value)>4:
        second=int(value[4:6])
    if len(value)>6:
        assert value[6]=='.'
        microsecond=int(value[7:])
    return datetime.time(hour,minute,second,microsecond)

# parses a DICOM datetime (VR DT)
def parsedatetime(value):
    tzinfo=None
    if '+' in value:
        value,suffix=value.split('+')
        assert len(suffix)==4
        tzinfo=tz(suffix,1)
    elif '-' in value:
        value,suffix=value.split('-')
        assert len(suffix)==4
        tzinfo=tz(suffix,-1)
    assert len(value)>=4
    year=int(value[:4])
    month=1
    day=1
    hour=0
    minute=0
    second=0
    microsecond=0
    if len(value)>4:
        month=int(value[4:6])
    if len(value)>6:
        day=int(value[6:8])
    if len(value)>8:
        hour=int(value[8:10])
    if len(value)>10:
        minute=int(value[10:12])
    if len(value)>12:
        second=int(value[12:14])
    if len(value)>14:
        assert value[14]=='.'
        microsecond=int(value[15:])
    return datetime.datetime(year,month,day,hour,minute,second,microsecond,tzinfo)

# parses a DICOM age (VR AS)
def parseduration(value):
    assert len(value)==4
    unit=value[-1]
    count=int(value[:-1])
    if unit=='D':
        value=str(count)+'DT0S'
    elif unit=='W':
        value=str(count*7)+'DT0S'
    elif unit=='M':
        value=str(count)+'MT0S'
    elif unit=='Y':
        value=str(count)+'Y0MT0S'
    else:
        assert False,unit
    return rdflib.Literal('P'+value,datatype=XSD.duration)

# returns the triple object for value with VR vr or None if not suitable
def tripleobject(vr,value):
    if vr in ('AE','CS','LO','SH'):
        value=unicode(value)
        value=value.strip(' ') # leading and trailing spaces insignificant
        value=cleantext(value)
        if value=='': # will almost always mean unknown -> drop
            return None
        return rdflib.Literal(value)
    elif vr in ('LT','ST','UT'):
        value=unicode(value)
        value=value.rstrip(' ') # trailing spaces insignificant
        value=cleantext(value)
        if value=='': # will almost always mean unknown -> drop
            return None
        return rdflib.Literal(value)
    elif vr=='PN':
        value=unicode(value)
        value=value.strip(' ') # leading and trailing spaces insignificant
        value=cleantext(value)
        if value=='': # will almost always mean unknown -> drop
            return None
        return rdflib.Literal(value)
    elif vr=='UI':
        return uritools.urifromuid(value)
    elif vr=='AS':
        value=unicode(value)
        value=cleantext(value)
        if value=='': # will almost always mean unknown -> drop
            return None
        return parseduration(value)
    elif vr=='IS':
        value=str(value)
        if value.strip()=='':
            return None
        value=int(value)
        assert type(value)==int
        return rdflib.Literal(long(value))
    elif vr=='DS':
        value=str(value)
        if value.strip()=='':
            return None
        return rdflib.Literal(float(value),datatype=XSD.double) 
    elif vr in ('FL','OF'):
        assert type(value)==float
        return rdflib.Literal(value,datatype=XSD.double)
    elif vr=='FD':
        assert type(value)==float
        return rdflib.Literal(value,datatype=XSD.double)
    elif vr in ('SL','SS','UL','US','US or SS'):
        # UL requires xsd:long!
        assert type(value) in (int,long),type(value)
        return rdflib.Literal(long(value))
    elif vr=='DA':
        value=str(value)
        if not value:
            return None
        return rdflib.Literal(parsedate(value))
    elif vr=='TM':
        value=str(value)
        if not value:
            return None
        return rdflib.Literal(parsetime(value))
        # rdf representation for missing seconds, hours ?
    elif vr=='DT':
        value=str(value)
        if not value:
            return None
        return rdflib.Literal(parsedatetime(value))
        # rdf representation for things missing after year ?
    elif vr=='UN':
        # represent UN as plain literal if possible
        try:
            value=unicode(value)
            value=value.strip(' ') # leading and trailing spaces insignificant
            value=cleantext(value)
        except Exception:
            return None
        if value=='': # will almost always mean unknown -> drop
            return None
        return rdflib.Literal(value)
    elif vr in ('OB','OW','OB or OW','OW or OB'):
        return None
    else:
        assert False,vr

def extratriples(graph,currentsubject,de,ie):
    if (de.VR=='PN' and de.tag==0x00100010 and ie=='Patient'):
        value=unicode(de.value)
        value=value.strip(' ') # leading and trailing spaces insignificant
        value=cleantext(value)
        if value=='': # will almost always mean unknown -> drop
            return None
        vs=value.split('=')[0].split('^')
        familyname=vs[0].strip()
        if familyname:
            graph.add((currentsubject,FOAF.familyName,rdflib.Literal(familyname)))
        if len(vs)>1:
            givenname=vs[1].strip()
            if givenname:
                graph.add((currentsubject,FOAF.givenName,rdflib.Literal(givenname)))

# get the single value for tag in dataset ds. check vr if supplied
def getsinglevalue(ds,tag,vr=None):
    value=None
    for de in ds:
        if de.tag==tag:
            if vr is not None:
                assert de.VR==vr
            assert de.VM==1
            assert value is None
            value=de.value
    return value

# generate a unique URI
def generateuri():
    global individualindex
    rand=random.randrange(999999)
    label=unicode(starttime).replace('.','-')+'-'+unicode(rand)+'-'+unicode(individualindex)  
    individualindex+=1
    return rdflib.URIRef(settings.individualns+label),label

# return URI of the current dataset + dictionary of IEs URIs + IOD name
def datasetcontext(graph,ds,set_label=True):
    ieuris={}
    iod=None

    uid=getsinglevalue(ds,0x00080018,'UI') # SOP Instance UID
    if uid is not None:
        subject=uritools.urifromuid(uid)
        label=str(uid)
    else:
        subject,label=generateuri()

    if set_label:
        graph.add((subject,RDFS.label,rdflib.Literal(label)))

    sopuid=getsinglevalue(ds,0x00080016,'UI') # SOP Class UID
    if sopuid is not None:
        uidstring=uritools.uidasstring(sopuid)
        if uidstring in sopclasses:
            iod=sopclasses[uidstring]
            for ie in iods[iod].keys():
                ieuris[ie]=None
        else:
            print >> sys.stderr, "SOP Class",uidstring,"not found"
        sopuiduri=uritools.urifromuid(sopuid)
        graph.add((subject,RDF.type,sopuiduri))

    return subject,ieuris,iod

# used in exceptions
def describedataelement(de):
    desc='type:'+str(type(de.value))
    desc+=' VM:'+str(de.VM)
    desc+=' VR:'+de.VR
    desc+=' tag:'+dicom.datadict.keyword_for_tag(de.tag)
    desc+=' value:'+str(de.value)
    return desc

# generate a URI for a IE and add some triples about it to the graph
# ds is the dataset the IE occured in and subject is the current context
# the IE should be connected with (normally the URI representing the 
# DICOM information object)
def getieuri(graph,subject,ds,ie):
    uidtag=None
    if ie=='Study':
        uidtag=0x0020000D
    elif ie=='Series':
        uidtag=0x0020000E
    elif ie=='Frame of Reference':
        uidtag=0x00200052

    uri=None
    if uidtag:
        uid=getsinglevalue(ds,uidtag,'UI')
        if uid is not None:
            uri=uritools.urifromuid(uid)
            label=str(uid)
    if not uri:
        uri,label=generateuri()

    graph.add((uri,RDF.type,uritools.getieclass(ie)))
    graph.add((uri,RDFS.label,rdflib.Literal(label)))
    graph.add((subject,DCTERMS.subject,uri))
    return uri

# generate triples from data element de in graph. iod is the current IOD
# and ieuris is the dictionary of IE URIs for this iod. subject is the current
# context and ds is the current dataset
def addtriples(graph,subject,ieuris,iod,de,ds):
    def gettagvalue(tag,vr):
        return getsinglevalue(ds,tag,vr)
    predicate=uritools.urifromtag(de.tag,gettagvalue=gettagvalue)
    currentsubject=subject

    if de.tag in dicom._dicom_dict.DicomDictionary:
        tagvm=dicom._dicom_dict.DicomDictionary[de.tag][1]
    else:
        tagvm='1'

    # try to determine IE and change currentsubject accordingly
    ie=None
    if iod and de.tag in iesbyattribute:
        if iod in iesbyattribute[de.tag]:
            matches=iesbyattribute[de.tag][iod]
        else: # attribute is not used in this IOD, see if IE is unique anyway
            matches=iesbyattribute[de.tag][None]
        if len(matches)==1:
            ie=matches[0]
            if ie not in ieuris:
                print >> sys.stderr,"IE",ie,"not in IOD for",iod
                ieuris[ie]=None
            currentsubject=ieuris[ie]
            if currentsubject is None:
                currentsubject=getieuri(graph,subject,ds,ie)
                ieuris[ie]=currentsubject

    if type(de.value)==dicom.sequence.Sequence:
        rdflist,dummy=generateuri()
        restlist=None
        graph.add((currentsubject,predicate,rdflist))
        for de1 in de:
            if restlist:
                graph.add((rdflist,RDF.rest,restlist))
                rdflist=restlist
            restlist,dummy=generateuri()
            object,ieuris1,iod1=datasetcontext(graph,de1)
            graph.add((rdflist,RDF.first,object))
            graph.add((rdflist,RDFS.label,rdflib.Literal('RDF List')))
            cl=uritools.urifromtag(de.tag,isclass=True,gettagvalue=gettagvalue)
            graph.add((object,RDF.type,cl))
            for de2 in de1:
                addtriples(graph,object,ieuris1,iod1,de2,de1)
        graph.add((rdflist,RDF.rest,RDF.nil))

    elif type(de.value) in (dicom.multival.MultiValue,list) or tagvm!='1':
        vr=de.VR
        if type(de.value) not in (dicom.multival.MultiValue,list):
            de=[de.value]
        rdflist,dummy=generateuri()
        restlist=None
        graph.add((currentsubject,predicate,rdflist))
        for de1 in de:
            object=tripleobject(vr,de1)
            if object is not None:
                if restlist:
                    graph.add((rdflist,RDF.rest,restlist))
                    rdflist=restlist
                restlist,dummy=generateuri()
                graph.add((rdflist,RDF.first,object))
                graph.add((rdflist,RDFS.label,rdflib.Literal('RDF List')))
        graph.add((rdflist,RDF.rest,RDF.nil))

    else:
        assert de.VM==1,describedataelement(de)
        object=tripleobject(de.VR,de.value)
        if object is not None:
            extratriples(graph,currentsubject,de,ie)
            graph.add((currentsubject,predicate,object))

# usage message
if len(sys.argv)==1:
    msg="""usage: dicom2rdf.py file1.dcm file2.dcm file3.dcm ...
will generate file1.rdf file2.rdf file3.rdf ...
"""
    sys.stderr.write(msg)
    sys.exit(1)

# main loop
for file in sys.argv[1:]:
    assert file.lower().endswith('.dcm')
    outfile=file[:-4]+'.rdf'
    ds=dicom.read_file(file)
    # convert encoded strings to unicode strings
    ds.decode()

    graph=uritools.newgraph()

    subject,ieuris,iod=datasetcontext(graph,ds.file_meta,set_label=False)
    assert not ieuris
    graph.add((subject,RDFS.label,rdflib.Literal(file)))
    mt=rdflib.URIRef('http://purl.org/NET/mediatypes/application/dicom')
    graph.add((subject,rdflib.URIRef('http://purl.org/dc/terms/format'),mt))
    for de in ds.file_meta:
        addtriples(graph,subject,ieuris,iod,de,ds.file_meta)

    subject,ieuris,iod=datasetcontext(graph,ds)
    for de in ds:
        addtriples(graph,subject,ieuris,iod,de,ds)

    outfile=open(outfile,"w")
    graph.serialize(outfile)
