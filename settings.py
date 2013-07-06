
import rdflib

# namespace for the ontology
ontons='http://purl.org/healthcarevocab/v1#'

# ontology prefix
ontoprefix='dicom'

# ontology document
ontodoc=rdflib.URIRef('http://purl.org/healthcarevocab/v1')

# namespace for OID-less entities described in DICOM files
# use '#' to generate fragment identifiers relative to the generated 
# RDF/XML-document
individualns='#'
