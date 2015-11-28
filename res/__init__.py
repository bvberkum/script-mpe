"""
res - Read metadata from metafiles.

Classes to represent a file or cluster of files from which specific metadata
may be derived. The objective is using this as a toolkit, to integrate into
programs that work on metadata and/or (media) files.

:XXX: three locations of metadir to bootstrap metadata framework: localdir,
    volumedir, or homedir.

TODO:
- Persist composite objects:
- Metalink reader/adapter. Metalink4 <-> HTTPResponseHeaders
- Content-* properties
"""
import os
import uuid
import anydbm
import shelve

from script_mpe import confparse
#from script_mpe import lib
#from script_mpe from taxus import get_session
from script_mpe import log

import iface
import util
from persistence import PersistedMetaObject
from fs import File, Dir
from mime import MIMEHeader
from metafile import Metafile, Metadir, Meta, SHA1Sum
from jrnl import Journal
from vc import Repo


"""

Registry
    handler class
        handler name ->

    Volume
        rsr:sha1sum
        rsr:sprssum

    Mediafile
        rsr:metafile
        txs:volume
        txs:workspace

"""


class Workspace(Metadir):

    """
    Workspaces are containers for specifically structured and tagged
    subtrees. Several subtypes are defined to deal with various types of working
    directories.

    Workspaces are metadirs with settings, loaded from DOTID '.yaml',
    and a PersistedMetaObject stored in DOTID '.shelve'.
    """

    DOTDIR = 'cllct'
    DOTID = 'ws'

    index_specs = [
        ]

    def __init__(self, path):
        super(Workspace, self).__init__(path)
        self.store = None
        self.indices = {}
        conf = self.metadirref('yaml')
        if os.path.exists(conf):
            self.settings = confparse.YAMLValues.load(conf)
        else:
            self.settings = {}

    @classmethod
    def get_session(klass, scriptname, scriptversion):
        """
        :FIXME:91: setup SA session:
            - load modules needed for script, possibly interdepent modules
            - assert data is at the required schema version using migrate
        """

    @property
    def dbref(self):
        return self.metadirref( 'shelve' )

    def init_store(self, truncate=False):
        assert not truncate
        return PersistedMetaObject.get_store(
                name=Metafile.storage_name, dbref=self.dbref)
        #return PersistedMetaObject.get_store(name=self.dotdir, dbref=self.dbref, ro=rw)
    # TODO: move this, res.dbm.MetaDirIndex
    def init_indices(self, truncate=False):
        flag = truncate and 'n' or 'c'
        idcs = {}
        for name in self.__class__.index_specs:
            ref = self.idxref(name)
            if ref.endswith('.db'):
                idx = anydbm.open(ref, flag)
            elif ref.endswith('.shelve'):
                idx = shelve.open(ref, flag)
            idcs[name] = idx
        return confparse.Values(idcs)


class Homedir(Workspace):

    """
    The default workspace for a user. If no other workspace type applies, the
    Homedir workspace has a user-configured, generic resource collection type.

    XXX: It is a workspace that is not a swappable, movable volume, but one that is
    fixed to a host and exists as long as the host system does.
    TODO: it shoud be aware of other host having a Homedir for current user.
    """

    DOTID = 'homedir'

    # XXX:
    htdocs = None # contains much of the rest of the personal workspace stuff
    projects = None # specialized workspace for projects..


class Workdir(Workspace):

    """
    A generic basedir ... ?
    """

    DOTID = 'local'


class Volumedir(Workspace):

    """
    A specific workspace used to distinguish media volumes (disk partitions,
    network drives, etc).
    """

    DOTID = 'vol'

    index_specs = [
                'sparsesum',
                'sha1sum',
                'dirs'
            ]

    def pathname(self, name, basedir=None):
        if basedir and basedir.startswith(self.path):
            path = basedir[len(self.path.rstrip('/'))+1:]
        else:
            path = ""
        return os.path.join(path, name)

    @classmethod
    def find(self, *paths):
        for idfile in Metadir.find(*paths):
            print idfile
            yield os.path.dirname( os.path.dirname( idfile ))



def read_unix(path):
    """
    Return true lines, dropping comments and whitespace lines.
    """
    r = []
    for l in open(path).readlines():
        if l.strip().startswith('#') or not l.strip():
            continue
        r.append(l.rstrip()) # leave indent
    return r

def read_idfile(path):
    """
    Return ID part and optional title part.
    """
    if not os.path.exists(path):
        raise Exception("UNID file missing %s" % path)
    idlines = read_unix(path)
    if not idlines:
        raise Exception("UNID missing in %s" % path)
    if len(idlines) > 1:
        raise Exception("Extraneous content in UNID file %s" % path)
    unid, title = idlines[0], None
    index = unid.find(' ')
    if index:
        unid, title = unid[:index], unid[index+1:]
    return unid, title

