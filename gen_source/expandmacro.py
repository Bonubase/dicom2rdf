import sys
sys.path.append('..')
import modulemacros

# return attributes within a module or macro specified by name
# macros will be expanded recursively
# contents of sequences will not be included
def expand(mm):
    if mm not in modulemacros.modulemacros:
        print >> sys.stderr, "macro",mm,"not found"
        return set()
    chapter,table,elements=modulemacros.modulemacros[mm]
    attributes=set()
    for element in elements:
        if type(element)==long: # attribute
            attributes.add(element)
        elif type(element)==str: # macro
            if element==mm:
                print >> sys.stderr, "macro",mm,"includes itself"
                continue
            attributes=attributes.union(expand(element))
        else: # tuple of (sequence,sequence item attributes)
            assert len(element)==2
            attributes.add(element[0])
    return attributes
