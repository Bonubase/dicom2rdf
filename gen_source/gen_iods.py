#!/usr/bin/python

import sys
from parse import gettables,currentchapter,gettag,ischapter
sys.path.append('..')
from modulemacros import *
from valid_ies import *

# functions to extract composite IODs

def getiods(s):
    rueck=[]
    for pos,tablename,tablenumber in gettables(s):
        if not tablenumber:
            continue
        if tablenumber[0]!='A':
            continue
        if tablename.upper().endswith(' IOD MODULES'):
            rueck.append((pos,tablename[:-8].upper()))
    return rueck

def getusage(s):
    found=False
    for usage in "MCU":
        for d in '\xad-':
            if s==usage or s.startswith(usage+' '+d) or s.startswith(usage+d):
                return usage
    return None

def normalize(line):
    if line.startswith(' '):
        line=line[1:]
    if line.startswith(' '):
        line=line[1:]
    while '   ' in line:
        line=line.replace('   ','  ')
    return line.split('  ')

def getmodules(lines):
    i=0
    modules={}
    currentie=None
    ignorenextie=False
    while i<len(lines):
        line=lines[i]
        i+=1
        parts=normalize(line)
        if len(parts)<4:
            continue
        if not ischapter(parts[2]):
            continue
        usage=getusage(parts[3])
        assert usage
        assert len(parts)==4,line

        if line.startswith('   '):
            assert currentie,line
            module=parts[1]
            reference=parts[2]
        else:
            ienew=parts[0]
            if ienew not in valid_ies:

                line1=lines[i]
                parts1=normalize(line1)
                ienew=ienew+' '+parts1[0]

                line2=lines[i+1]
                parts2=normalize(line2)

                if ienew+' '+parts2[0] in valid_ies:
                    ienew=ienew+' '+parts2[0]
                    lines[i]='  '.join(parts1[1:])
                    lines[i+1]='  '.join(parts2[1:])
                elif ienew in valid_ies:
                    lines[i]='  '.join(parts1[1:])
                else:
                    assert False,line+'\n'+line1+'\n'+line2
            currentie=ienew
            module=parts[1]
            reference=parts[2]

        if module.upper() in ('OVERLAY PLANE','MULTI-FRAME OVERLAY','OVERLAY ACTIVATION'):
            continue

        if module.upper()+' MODULE' in modulemacros:
            module=module.upper()+' MODULE'
        elif reference in modulesbychapter:
            matches=modulesbychapter[reference]
            assert len(matches)==1,line
            module=matches[0]
        else:
            matches=[]
            for chapter in modulesbychapter:
                if chapter.startswith(reference+'.'):
                    matches.append(chapter)
            assert len(matches)==1,line
            matches=modulesbychapter[matches[0]]
            assert len(matches)==1,line
            module=matches[0]
        if currentie in modules:
            modules[currentie].append((module,usage))
        else:
            modules[currentie]=[(module,usage)]
    return modules

# functions to extract normalized IODs

def getiename(s):
    assert s.endswith(' IOD')
    s=s[:-4]
    rueck=''
    for word in s.split():
        word=word[:1]+word[1:].lower()
        rueck+=word+' '
    return rueck[:-1]

def getiods1(s):
    rueck=[]
    for pos,tablename,tablenumber in gettables(s):
        if not tablenumber:
            continue
        if tablenumber[0]!='B':
            continue
        if tablename.upper().endswith(' IOD MODULES'):
            rueck.append((pos,tablename[:-8].upper()))
    return rueck

def normalize1(line):
    line=line.lstrip()
    while '   ' in line:
        line=line.replace('   ','  ')
    return line.split('  ')

def getmodules1(lines):
    i=0
    modules=[]
    while i<len(lines):
        line=lines[i]
        i+=1
        parts=normalize1(line)
        if len(parts)<3:
            continue
        if not ischapter(parts[1]):
            continue
        assert len(parts)==3,line

        module=parts[0].upper()

        if module in ('OVERLAY PLANE','MULTI-FRAME OVERLAY','OVERLAY ACTIVATION'):
            continue

        reference=parts[1]
        if module+' MODULE' in modulemacros:
            module=module+' MODULE'
        elif reference in modulesbychapter:
            matches=modulesbychapter[reference]
            assert len(matches)==1,line
            module=matches[0]
        else:
            matches=[]
            for chapter in modulesbychapter:
                if chapter.startswith(reference+'.'):
                    matches.append(chapter)
            assert len(matches)==1,line
            matches=modulesbychapter[matches[0]]
            assert len(matches)==1,line
            module=matches[0]
        modules.append((module,'M'))
    return modules


print "# dictionary of IODs by name"
print "# values are a dictionary: key=IE name, value=list of (module,usage) tuples"
print "iods={"

f=open('11_03pu.txt',"r")
text=f.read()
f.close()
seen=set()

# composite IODs
tables=getiods(text)
i=0
while i<len(tables):
    pos,tablename=tables[i]
    assert tablename
    assert tablename not in seen
    seen.add(tablename)
    if i==len(tables)-1:
        nextpos=len(text)-1
    else:
        nextpos=tables[i+1][0]
    pages=0
    snippet=currentchapter(text[pos:nextpos])
    modules=getmodules(snippet)
    assert modules
    print repr(tablename)+': '+repr(modules)+','
    print 
    i+=1

# normalized IODs
tables=getiods1(text)
i=0
while i<len(tables):
    pos,tablename=tables[i]
    assert tablename
    assert tablename not in seen
    seen.add(tablename)
    assert getiename(tablename) in valid_ies
    if i==len(tables)-1:
        nextpos=len(text)-1
    else:
        nextpos=tables[i+1][0]
    pages=0
    snippet=currentchapter(text[pos:nextpos])
    modules=getmodules1(snippet)
    assert modules
    modules={getiename(tablename):modules}
    print repr(tablename)+': '+repr(modules)+','
    print
    i+=1

print "}"
