
import rdflib

# namespace for the ontology
ontons='http://purl.org/healthcarevocab/v1#'

# ontology document
ontodoc=rdflib.URIRef('http://purl.org/healthcarevocab/v1')

# ontology creator
ontocreator=rdflib.URIRef('http://www.brunni.de/foaf.rdf#me')

# namespace for OID-less entities described in DICOM files
# use '#' to generate fragment identifiers relative to the generated 
# RDF/XML-document
individualns='#'
