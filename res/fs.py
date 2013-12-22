from fnmatch import fnmatch
import os
from os.path import dirname, join, basename, isdir
import re
import stat

import confparse
import log
from lib import Prompt


PATH_R = re.compile("[A-Za-z0-9\/\.,\[\]\(\)_-]")

class File(object):

    ignore_names = (
            '._*',
            '.crdownload',
            '.DS_Store',
            '*.swp',
            '*.swo',
            '*.swn',
            '*.r[0-9]*[0-9]',
            '.git*',
        )

    ignore_paths = (
            '*.pyc',
            '*~',
            '*.part',
            '*.incomplete',
            '*.crdownload',
        )

    include_paths = (
            '*.ogg', 
            '*.mp3', 
            '*.jpg', 
            '*.pdf', 
            '*.mkv', 
            '*.mp4', 
            '*.wmv', '*.mpg', '*.avi'
        )
    include_names = (
        )

    @classmethod
    def sane(klass, path):
        return PATH_R.match(path)

    @classmethod
    def include(klass, path):
        for p in klass.include_paths:
            if fnmatch(path, p):
                return True
        name = basename(path)
        for p in klass.include_names:
            if fnmatch(name, p):
                return True

    @classmethod
    def ignored(klass, path):
        for p in klass.ignore_paths:
            if fnmatch(path, p):
                return True
        name = basename(path)
        for p in klass.ignore_names:
            if fnmatch(name, p):
                return True


class Dir(object):

    sysdirs = (
            '/usr/share/cllct',
            '/var/lib/cllct',
            '/etc/cllct',
            '*/.cllct',
            '*/.volume',
        )

    ignore_names = (
            '._*',
            '.metadata',
            '.conf',
            'RECYCLER',
            '.TemporaryItems',
            '.Trash*',
            'cllct',
            '.cllct',
            'System Volume Information',
            'Desktop',
            'project',
            'sam*bup*',
            '*.bup',
            '.git*',
        )

    ignore_paths = (
            '*.git',
        )

    @classmethod
    def issysdir( klass, path ):
        path = path.rstrip( os.sep )
        for p in klass.sysdirs:
            if fnmatch( path, p ):
                return True

    @classmethod
    def sane( klass, path ):
        return PATH_R.match( path )

    @classmethod
    def ignored(klass, path):
        for p in klass.ignore_paths:
            if fnmatch(path, p):
                return True
        name = basename(path)
        for p in klass.ignore_names:
            if fnmatch(name, p):
                return True

    @classmethod
    def prompt_recurse(clss, opts):
        v = Prompt.query("Recurse dir?", ("Yes", "No", "All"))
        if v is 2:
            opts.recurse = True
            return True
        elif v is 0:
            return True
        return False

    walk_opts = confparse.Values(dict(
        interactive=False,
        recurse=False,
        max_depth=-1,
    ))
    @classmethod
    def walk(Klass, path, opts=walk_opts, filters=(None,None)):
        if opts.max_depth > 0:
            assert opts.recurse
        dirpath = None
        left = []
        file_filters, dir_filters = filters
        for root, dirs, files in os.walk(path): # XXX; does not use StatCache
            if root not in left:
                left.append( root )
                yield unicode( root, 'utf-8' )
            for node in list(dirs):
                if not opts.recurse and not opts.interactive:
                    dirs.remove(node)
                    continue
                dirpath = join(root, node)
                if dir_filters:
                    brk = False
                    for fltr in dir_filters:
                        if not fltr(dirpath):
                            dirs.remove(node)
                            brk = True
                            break
                    if brk:
                        continue
                if not StatCache.exists(dirpath):
                    log.err("Error: reported non existant node %s", dirpath)
                    dirs.remove(node)
                    continue
                depth = dirpath.replace(path,'').strip('/').count('/')
                if Klass.ignored(dirpath):
                    log.info("Ignored directory %r", dirpath)
                    dirs.remove(node)
                    continue
                elif opts.max_depth != -1 and depth >= opts.max_depth:
                    dirs.remove(node)
                    continue
                elif opts.interactive:
                    log.note("Interactive walk: %s", dirpath)
                    if not Klass.prompt_recurse(opts):
                        dirs.remove(node)
                assert isinstance(dirpath, basestring)
                try:
                    dirpath = unicode(dirpath, 'utf-8')#
#                dirpath = dirpath.decode('utf-8')
                except UnicodeDecodeError, e:
                    log.warn("Ignored non-unicode path %s", dirpath)
                    continue
                assert isinstance(dirpath, unicode)
                #try:
                #    dirpath.encode('ascii')
                #except UnicodeDecodeError, e:
                #    log.warn("Ignored non-ascii path %s", dirpath)
                #    continue
            #    yield dirpath

            for leaf in list(files):
                filepath = join(root, leaf)
                if file_filters:
                    brk = False
                    for fltr in file_filters:
                        if not fltr(filepath):
                            files.remove(leaf)
                            brk = True
                            break
                    if brk:
                        continue
                if not StatCache.exists(filepath):
                    log.warn("Error: non existant leaf %s", filepath)
                    continue
                if StatCache.islink(filepath) or not StatCache.isfile(filepath):
                    log.note("Ignored non-regular file %r", filepath)
                    continue
                if File.ignored(filepath):
                    log.info("Ignored file %r", filepath)
                    continue
                assert isinstance(filepath, basestring)
                try:
                    filepath = unicode(filepath, 'utf-8')
                except UnicodeDecodeError, e:
                    log.warn("Ignored non-unicode filename %s", filepath)
                    continue
                assert isinstance(filepath, unicode)
#                try:
#                    filepath.encode('ascii')
#                except UnicodeEncodeError, e:
#                    log.warn("Ignored non-ascii/illegal filename %s", filepath)
#                    continue
                yield filepath
            #yield dirname( dirpath )
    @classmethod
    def find_newer(Klass, path, path_or_time):
        if StatCache.exists(path_or_time):
            path_or_time = StatCache.getmtime(path_or_time)
        def _isupdated(path):
            return StatCache.getmtime(path) > path_or_time
        for path in clss.walk(path, filters=[_isupdated]):
            yield path

    @classmethod
    def find_newer(Klass, path, path_or_time):
        if StatCache.exists( path_or_time ):
            path_or_time = StatCache.getmtime(path_or_time)
        def _isupdated(path):
            return StatCache.getmtime(path) > path_or_time
        for path in clss.walk(path, filters=[_isupdated]):
            yield path

class StatCache:
    paths = {}
    @classmethod
    def init( clss, path ):
        if isinstance( path, unicode ):
            path = path.encode( 'utf-8' )
        p = path
        if path in clss.paths:
            v = clss.paths[ path ]
            if isinstance( v, str ): # shortcut to dirpath (w/ trailing sep)
                p = v
                v = clss.paths[ p ]
        else:    
            v = os.lstat( path )
            if stat.S_ISDIR( v.st_mode ):
                # store shortcut to normalized path
                if path[ -1 ] != os.sep:
                    p = path + os.sep
                    clss.paths[ path ] = p
                else:
                    p = path
                    clss.paths[ path.rstrip( os.sep ) ] = path
            assert isinstance( path, str )
            clss.paths[ p ] = v
        assert isinstance( p, str )
        return p.decode( 'utf-8' )
    @classmethod
    def getsize( clss, path ):
        p = clss.init( path ).encode( 'utf-8' )
        return clss.paths[ p ].st_size
    @classmethod
    def exists( clss, path ):
        try:
            p = clss.init( path )
        except:
            return
        return True
    @classmethod
    def getmtime( clss, path ):
        p = clss.init( path ).encode( 'utf-8' )
        return clss.paths[ p ].st_mtime
    @classmethod
    def isdir( clss, path ):
        p = clss.init( path ).encode( 'utf-8' )
        return stat.S_ISDIR( clss.paths[ p ].st_mode )
    @classmethod
    def isfile( clss, path ):
        p = clss.init( path ).encode( 'utf-8' )
        return stat.S_ISREG( clss.paths[ p ].st_mode )
    @classmethod
    def islink( clss, path ):
        p = clss.init( path ).encode( 'utf-8' )
        return stat.S_ISLNK( clss.paths[ p ].st_mode )

