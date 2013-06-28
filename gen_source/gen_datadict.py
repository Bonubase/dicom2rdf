#!/usr/bin/python

missing={
0x0040E020: ('CS', '1', "Type of Instances", '', 'TypeOfInstances'),
0x0040E021: ('SQ', '1', "DICOM Retrieval Sequence", '', 'DICOMRetrievalSequence'),
0x0040E022: ('SQ', '1', "DICOM Media Retrieval Sequence", '', 'DICOMMediaRetrievalSequence'),
0x0040E023: ('SQ', '1', "WADO Retrieval Sequence", '', 'WADORetrievalSequence'),
0x0040E024: ('SQ', '1', "XDS Retrieval Sequence", '', 'XDSRetrievalSequence'),
0x0040E030: ('UI', '1', "Repository Unique ID", '', 'RepositoryUniqueID'),
0x0040E031: ('UI', '1', "Home Community ID", '', 'HomeCommunityID'),
0x00221009: ('CS', '1', "Ophthalmic Axial Measurements DeviceType", '', 'OphthalmicAxialMeasurementsDeviceType'),
0x00221012: ('SQ', '1', "Ophthalmic Axial Length Sequence", '', 'OphthalmicAxialLengthSequence'),
0x00221095: ('LO', '1', "Implant Name", '', 'ImplantName'),
0x00221097: ('LO', '1', "Implant Part Number", '', 'ImplantPartNumber'),
0x00221127: ('SQ', '1', "Lens Thickness Sequence", '', 'LensThicknessSequence'),
0x00221128: ('SQ', '1', "Anterior Chamber Depth Sequence", '', 'AnteriorChamberDepthSequence'),
0x00221134: ('SQ', '1', "Source of Refractive Measurements Sequence", '', 'SourceofRefractiveMeasurementsSequence'),
0x00282144: ('LO', '1-n', "Lossy Image Compression Method", '', 'LossyImageCompressionMethod'),
0x00280304: ('UI', '1', "Referenced Color Palette Instance UID", '', 'ReferencedColorPaletteInstanceUID'),
}

import dicom
from parse import hextag

datadict={}
for tag,value in dicom._dicom_dict.DicomDictionary.items():
    tag=long(tag)
    if not tag & 0xffff0000:
        continue
    datadict[tag]=value

for tag,value in missing.items():
    tag=long(tag)
    assert tag not in datadict
    datadict[tag]=value

print """# DICOM data dictionary
# values are tuples of VR,VM,Name,Retired,Keyword
#
# This dictionary has been generated using the pydicom Python module:
# http://code.google.com/p/pydicom/
#
# Portions of pydicom (private dictionary file(s)) were generated from the
# private dictionary of the GDCM library, released under the following 
# license:
#
# Program: GDCM (Grassroots DICOM). A DICOM library
# Module: http://gdcm.sourceforge.net/Copyright.html
#
# Copyright (c) 2006-2010 Mathieu Malaterre
# Copyright (c) 1993-2005 CREATIS
# (CREATIS = Centre de Recherche et d'Applications en Traitement de l'Image)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are 
# met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# * Neither name of Mathieu Malaterre, or CREATIS, nor the names of any
# contributors (CNRS, INSERM, UCB, Universite Lyon I), may be used to
# endorse or promote products derived from this software without specific
# prior written permission.
#
"""

print "datadict={"

for tag,value in datadict.items():
    tag=hextag(tag)
    print tag+": "+repr(value)+","

print """}

def keyword_for_tag(tag):
    tag=long(tag)
    if tag in datadict:
        return datadict[tag][4]
    return ''
"""
