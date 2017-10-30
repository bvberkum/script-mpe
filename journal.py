#!/usr/bin/env python
""":created: 2017-05-08
"""
from __future__ import print_function

__description__ = "journal - "
__version__ = '0.0.4-dev' # script-mpe
__couch__ = 'http://localhost:5984/the-registry'
__usage__ = """
Usage:
    journal.py [options] [ LIST ]
    journal.py couchlog --date DATE
    journal.py couchlog --path PATH [BITS]
    journal.py couchlog [--current|--latest|--dev] [PATH]
    journal.py -h|--help
    journal.py --version

Options:
    --couch=REF
                  Couch DB URL [default: %s]
    --verbose     ..
    --quiet       ..
    -h --help     Show this usage description.
    --version     Show version (%s).

""" % ( __couch__, __version__ )

import os

import libcmd_docopt
import res.jrnl

from taxus.init import SqlBase, get_session
from taxus import Node, Topic
from res import Journal

import couchdb


models = [ Node, Topic, Journal ]


def cmd_journal_rw(LIST, opts, settings):
    entries = res.jrnl.JournalTxtManifestParser()
    print(entries)
    if LIST:
        assert os.path.exists(LIST), LIST
        list(entries.load_file(LIST))
    for k in entries.be:
        print(k, end='')
        print(entries[k])


def cmd_journal_couch(PATH, opts, settings):
    jrnl = Journal.find(PATH)


def cmd_couchlog(opts, settings):
    """
    TODO: keep an audit type log, with path references.

    Query:

        journal couchlog --date today # list entries
        journal couchlog --path [<prefix>:]/<path> # show entry

        journal couchlog --current # list all paths marked as local working setup
        journal couchlog --latest # list paths marked as latest available
        journal couchlog --dev # list paths marked as local dev

        deleted, moved, copied

    Update:

        journal couchlog --current <path>
        journal couchlog --latest <path>
        journal couchlog -m "Imported to boreas SQL" <path>

    Data:
        message:
        markers: current/latest
        state: dev/deleted/copy
        paths: [..]
        datestamp:
    """

    ref, dbname = settings.couch.rsplit('/', 1)
    opts.flags.couchdb = dbname
    #print(ref, dbname)

    server = couchdb.client.Server(ref)
    db = server[opts.flags.couchdb]
    print(server, db)

    for it in db:
        print(it)

    #if opts.flags.date
    #if opts.flags.path
    #if opts.arguments.path


### Transform cmd_ function names to nested dict

commands = libcmd_docopt.get_cmd_handlers_2(globals(), 'cmd_')
commands['help'] = libcmd_docopt.cmd_help


### Util functions to run above functions from cmdline

def main(opts):

    """
    Execute command.
    """

    settings = opts.flags
    opts.default = 'journal-rw'
    return libcmd_docopt.run_commands(commands, settings, opts)

def get_version():
    return 'journal.mpe/%s' % __version__

if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')

    couch = os.getenv( 'COUCH_DB', __couch__ )
    if couch is not __couch__:
        __usage__ = __usage__.replace(__couch__, couch)

    opts = libcmd_docopt.get_opts(__description__ + '\n' + __usage__, version=get_version())
    sys.exit(main(opts))
