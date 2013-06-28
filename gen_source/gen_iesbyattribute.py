#!/usr/bin/python

import sys
sys.path.append('..')
from parse import hextag
from expandmacro import expand

from datadict import *
from modulemacros import *
from iods import *

# check for infinite recursions
for mm in modulemacros:
    expand(mm)

iesbyattribute={}
for iod,ioddict in iods.items():
    for ie,modules in ioddict.items():
        for module,usage in modules:
            for attribute in expand(module):
                if attribute in iesbyattribute:
                    if ie not in iesbyattribute[attribute][None]:
                        iesbyattribute[attribute][None].append(ie)
                    if iod in iesbyattribute[attribute]:
                        if ie not in iesbyattribute[attribute][iod]:
                            iesbyattribute[attribute][iod].append(ie)
                    else:
                        iesbyattribute[attribute][iod]=[ie]
                else:
                    iesbyattribute[attribute]={None:[ie],iod:[ie]}

print "# list of possible IEs for an attribute by attribute and IOD name"
print "# (2-dimensional dictionary)"
print "# The key None for the IOD yields all possible IEs for the attribute"
print "# regardless of IOD context"
print "iesbyattribute={"

for tag,iedict in iesbyattribute.items():
    print '# '+keyword_for_tag(tag)
    print hextag(tag)+': {'
    
    for key,value in iedict.items():
        print ' '+repr(key)+': '+repr(value)+','
        if key!=None and len(value) > 1:
            print >> sys.stderr,"tag",hextag(tag),"not unique in",key,":",value
    print '},'
print "}"
