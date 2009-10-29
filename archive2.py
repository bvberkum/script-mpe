import sys, os, re


cwd='/home/berend/htdocs/'#os.getcwd()
arch='/home/berend/cabinet/'
ignore=(
    '/home/berend/htdocs/Makefile',
    '/home/berend/htdocs/.Rules.iris.mk',
    '/home/berend/htdocs/.Rules.sam.mk',
    '/home/berend/htdocs/main.rst',
    '/home/berend/htdocs/sysadmin.rst',
    '/home/berend/htdocs/sysadmin.sam.rst',
    '/home/berend/htdocs/sysadmin.iris.rst',
    '/home/berend/htdocs/sysadmin.ariaweg.rst',
    '/home/berend/htdocs/sysadmin.oostereind.rst',
    '/home/berend/htdocs/.bzr',
        )
delimiter=re.compile('[\/\._\[\]\(\),\+-]')
illegal=re.compile('[\ ~:\$\&\"\'\*]')
maxsize=10*1024**2


def archived(path):
    dates=[]
    parts=delimiter.split(path)
    year, month, day = None, None, None
    while parts:
        part=parts.pop(0)
        if part.isdigit():
            if not year and len(part)==4:
                year=part
            elif len(part)==2:
                if not month:
                    month=part
                else:
                    day=part
        if year and month and day:
            dates.append((year, month, day))
            year, month, day = None, None, None
    return dates

def isarchive(path):
    return len(archived(path)) == 1

def archive(path, root):
    pass


for root, dirs, files in os.walk(cwd):
    for name in dirs + files:
        cpath = os.path.join(root, name)

        skip = cpath in ignore
        if skip:
            print >>sys.stderr, 'Ingoring %s' % cpath
        else:            
            skip = illegal.search(cpath) is not None
            if skip:
                print >>sys.stderr, 'Illegal characters in %s' % cpath
            elif os.path.isfile(cpath):
                skip = 0 > os.path.getsize(cpath) > maxsize
                if skip:
                    print >>sys.stderr, 'File too large: %s' % cpath

        if skip:
            if os.path.isdir(cpath):
                dirs.remove(name)
            else:
                files.remove(name)

        if not isarchive(cpath):
            print archived(cpath), cpath
            #archive(cpath, arch)
        else:
            print archived(cpath), cpath


