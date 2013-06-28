
import sys

def hextag(tag):
    assert type(tag)==long
    keyword=hex(tag).upper()
    assert keyword.startswith('0X')
    assert keyword.endswith('L')
    keyword=keyword[2:-1]
    while len(keyword)<8:
        keyword='0'+keyword
    return '0x'+keyword+'L'

def gettag(s):
    if not s.startswith('('):
        return None
    if not s.endswith(')'):
        return None
    s=s[1:-1].split(',')
    if len(s)!=2:
        return None
    if len(s[0])!=4 or len(s[1])!=4:
        return None
    tag=s[0]+s[1]
    try:
        tag=long(tag,16)
    except Exception:
        print >> sys.stderr,"invalid tag",tag
        pass
    return tag

def ischapter(s):
    if len(s)>=2 and s[1]=='.' and s[0] in "ABC":
        s=s[2:]
    if not s:
        return False
    for c in s:
        if c not in "0123456789.":
            return False
    return True

# returns the chapter number if this line opens a new chapter
def isnewchapterline(line):
    line1=line.lstrip()
    tagfound=False
    for tag in line1.split():
        if gettag(tag) is not None:
            tagfound=True
    if not tagfound and line.count(' ')<40 and len(line1)>2:
        parts=line1.split()
        if len(parts)>1 and parts[1].strip():
            if ischapter(parts[0]):
                return parts[0]
    return None

# returns last chapter at the end of the text
def lastchapter(s):
    lines=s.split('\n')
    i=len(lines)-1
    while i>=0:
        line=lines[i]
        i-=1
        chapter=isnewchapterline(line)
        if chapter:
            return chapter
    assert False

# returns s truncated to the current chapter
def currentchapter(s):
    lines=[]
    for page in s.split('\f'):
        for line in page.split('\n'):
            if isnewchapterline(line):
                return lines
            lines.append(line)
    return lines

def gettables(s):
    pos=0
    rueck=[]
    while s.find('Table ',pos) >= 0:
        pos=s.find('Table ',pos)+6
        tablename=''
        pos1=s.find(' ',pos)
        assert pos1>0
        tablenumber=s[pos:pos1].strip()
        while s[pos1] not in '\r\n':
            tablename+=s[pos1]
            pos1+=1
        tablename=tablename.strip()
        if len(tablename)<2:
            continue
        if tablename[-1].isalpha() and tablename[-2]==' ':
            tablename=tablename[:-2]
        if tablename.startswith('- '):
            tablename=tablename[2:]
        found=False
        for c in tablename:
            if c.isalpha():
                found=True
                break
        if not found:
            continue
        if tablenumber.endswith('--RT'):
            tablename='RT '+tablename
            tablenumber=tablenumber[:-4]
        rueck.append((pos,tablename,tablenumber))
    return rueck
