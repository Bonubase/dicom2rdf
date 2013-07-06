import sys
import dicom,rdflib,urllib
import settings,datadict

# get class URI for IE name
def getieclass(ie):
    uri=settings.ontons+'IE.'+ie.replace(' ','')
    return rdflib.URIRef(uri)

# convert pydicom OID/UID to string
def uidasstring(uid):
    if type(uid)==dicom.UID.UID:
        uid=repr(uid).split("'")[1]
    assert uid
    for c in uid:
        assert c in "0123456789.",uid
    return uid

# generate OID URI from OID string
def urifromuid(uid):
    uid=uidasstring(uid)
    return rdflib.URIRef('urn:oid:'+uid)

# generate attribute URI from integer or pydicom BaseTag
# generate sequence item URI for sequence item attribute if isclass=True
def urifromtag(tag,isclass=False,numeric=False,gettagvalue=None):
    assert type(tag) in (int,long,dicom.tag.BaseTag),type(tag)
    if type(tag)!=dicom.tag.BaseTag:
        tag=dicom.tag.Tag(long(tag))

    if tag.group%2 and tag.element >= 0x1000:
        # private data element
        assert gettagvalue is not None,tag
        implementortag=dicom.tag.Tag(tag.group,tag.element >> 8)
        implementor=gettagvalue(implementortag,vr='LO')
        assert implementor,tag
        implementor=unicode(implementor)
        implementor=implementor.replace(' ','')
        implementor=urllib.quote(implementor.encode('utf8')).replace('%','$')
        keyword=hex(long(tag) & 0xffff00ff).upper()
        assert keyword.startswith('0X')
        assert keyword.endswith('L')
        keyword=keyword[2:-1]   
        while len(keyword)<8:
            keyword='0'+keyword
        keyword='PTag.'+implementor+'.'+keyword[:4]+'.'+keyword[4:]
    else:
        # normal data element
        keyword=hex(long(tag)).upper()
        assert keyword.startswith('0X')
        assert keyword.endswith('L')
        keyword=keyword[2:-1]
        while len(keyword)<8:
            keyword='0'+keyword
        keyword='Tag.'+keyword[:4]+'.'+keyword[4:]

        if not numeric:
            keyword1=datadict.keyword_for_tag(tag)
            if keyword1:
                for c in keyword1:
                    assert c.isalnum(),keyword1
                keyword=keyword1
            else:
                print >> sys.stderr, "Keyword for tag",str(tag),"not found"

    uri=settings.ontons
    if isclass:
        uri+='SequenceItem.'
    uri+=keyword
    return rdflib.URIRef(uri)

# create new rdflib graph with predefined prefixes
def newgraph():
    graph=rdflib.Graph()
    graph.bind('rdf',rdflib.namespace.RDF)
    graph.bind('rdfs',rdflib.namespace.RDFS)
    graph.bind('owl',rdflib.namespace.OWL)
    graph.bind(settings.ontoprefix,rdflib.namespace.Namespace(settings.ontons))
    graph.bind('dcterms',rdflib.namespace.Namespace('http://purl.org/dc/terms/'))
    graph.bind('foaf',rdflib.namespace.Namespace('http://xmlns.com/foaf/0.1/'))
    graph.bind('co',rdflib.namespace.Namespace('http://purl.org/co/'))
    return graph
