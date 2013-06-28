#!/usr/bin/python

import sys
sys.path.append('..')
from parse import *
from datadict import *

macro_corrections={
'OPHTHALMIC VISUAL FIELD GLOBAL INDEX MACRO C8263-2':'OPHTHALMIC VISUAL FIELD GLOBAL INDEX MACRO',
'TABLE 10-23 EXPOSURE INDEX MACRO':'EXPOSURE INDEX MACRO',
'CODE SEQUENCE MACRO (TABLE 88-1)':'CODE SEQUENCE MACRO',
'BASIC PIXEL SPACING CALIBRATION MACRO (TABLE 10-10)':'BASIC PIXEL SPACING CALIBRATION MACRO',
'VISUAL ACUITY MEASUREMENT MACRO':'VISUAL ACUITY MEASUREMENTS MACRO',
}

chapter_corrections={
'ENHANCED GENERAL EQUIPMENT MODULE':'C.7.5.2',
'HANGING PROTOCOL ENVIRONMENT MODULE':'C.23.2',
}

def gettags(lines,nesting=0):
    tags=[]

    while lines:
        line=lines.pop(0)
        line1=line.lstrip()  
        realnesting=0
        while line1 and line1[0]=='>':
            line1=line1[1:]
            realnesting+=1

        tagfound=False
        # we assume that a tag in the table has 2 leading and trailing WS
        for word in line.split('  '):
            tag=gettag(word.strip())
            if type(tag)==long:
                assert not tagfound
                tagfound=True

                assert realnesting<=nesting,line
                if realnesting<nesting:
                    lines.insert(0,line)
                    return tags

                assert tag in datadict,hex(tag)
                vr=datadict[tag][0]

                #print hex(tag),vr

                if vr=='SQ':
                    tags.append((tag,gettags(lines,nesting=nesting+1)))
                else:
                    if tag not in tags:
                        tags.append(tag)
        if tagfound:
            continue

        if line1.startswith('Include '):
            line1=line1[8:]
            line1=line1.split('  ')[0]
            if ' Table' in line1:
                line1=line1[:line1.find(' Table')]
            for c in "'`\".,":
                line1=line1.replace(c,'')
            line1=line1.strip()
            line1=line1.upper()
            if line1 in macro_corrections:
                line1=macro_corrections[line1]

            if line1.startswith('ONE OR MORE FUNCTIONAL GROUP MACROS'):
                pass
            elif line1.startswith('ANY PRIVATE ATTRIBUTES THAT'):
                pass
            elif line1.endswith(' MACRO'):

                assert realnesting<=nesting,line
                if realnesting<nesting: 
                    lines.insert(0,line)
                    return tags

                assert line1 not in tags
                tags.append(line1)
            else:
                assert False,line

    return tags

def getmodulemacros(s):
    rueck=[]
    for pos,tablename,tablenumber in gettables(s):
        if tablename.endswith(' ATTRIBUTES'):
            rueck.append((pos,tablenumber,tablename[:-11].upper()))
        elif tablename.endswith(' MODULE'):
            rueck.append((pos,tablenumber,tablename))
        elif tablename.endswith(' MACRO'):
            rueck.append((pos,tablenumber,tablename.upper()))
        elif tablename.endswith(' Macro Attributes Description'):
            rueck.append((pos,tablenumber,tablename[:-23].upper()))
        elif tablename.endswith(' Macro Attributes'):
            rueck.append((pos,tablenumber,tablename[:-11].upper()))
        elif tablename.endswith(' Module Attributes'):
            rueck.append((pos,tablenumber,tablename[:-11].upper()))
        elif tablename=='Common Attribute Set for Code Sequence Attributes':
            rueck.append((pos,tablenumber,"Code Sequence Macro".upper()))
        elif tablename=='OPHTHALMIC AXIAL MEASUREMENTS QUALITY IMAGE SOP INSTANCE REFERENCE':
            rueck.append((pos,tablenumber,tablename+' MACRO'))
        #elif tablename in ('PALETTE COLOR LOOKUP MODULE','GRAPHIC GROUP MODULE'):
        #    rueck.append((pos,tablenumber,tablename))
        elif tablename=='Enhanced XA/XRF Image Module Table':
            rueck.append((pos,tablenumber,tablename[:-6].upper()))
    return rueck

def reprtags(elements):
    reprlist='['
    for element in elements:
        if type(element) == long:
            item=hextag(element)
        elif type(element) == str:
            item=repr(element)
        else:
            ht=hextag(element[0])
            recursivelist=reprtags(element[1])
            if recursivelist=='[]':
                print >> sys.stderr,"empty list for sequence",ht
            item='('+ht+', '+recursivelist+')'
        reprlist+=item+', '
    if elements:
        reprlist=reprlist[:-2]
    reprlist+=']'
    return reprlist

print "# dictionary of modules and macros by name"
print "# values are tuples of (chapter,table number,element list)"
print "# element list contains tags, macro names or tuples for sequence tags:"
print "#  (tag,nested element list)"
print "modulemacros={"

f=open('11_03pu.txt',"r")
text=f.read()
f.close()
tables=getmodulemacros(text)
modulesbychapter={}
seen=set()
i=0
while i<len(tables):
    pos,tablenumber,tablename=tables[i]
    assert tablename
    assert tablenumber
    if i==len(tables)-1:
        nextpos=len(text)-1
    else:
        nextpos=tables[i+1][0]
    pages=0
    i+=1
    snippet=currentchapter(text[pos:nextpos])
    chapter=lastchapter(text[:pos])
    tags=gettags(snippet)
    if not tags:
        continue
    assert tablename not in seen
    seen.add(tablename)
    if tablename in chapter_corrections:
        chapter=chapter_corrections[tablename]
    if tablename.endswith(' MODULE'):    
        if chapter in modulesbychapter:
            modulesbychapter[chapter].append(tablename)
        else:
            modulesbychapter[chapter]=[tablename]

    print repr(tablename)+': ('+repr(chapter)+','+repr(tablenumber)+',',reprtags(tags)+'),'
    print

print "}"

print "modulesbychapter={"
for key,value in modulesbychapter.items():
    print repr(key)+': '+repr(value)+','
print "}"
