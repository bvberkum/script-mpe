#!/usr/bin/env python
"""
:Created: 2015-12-27

Usage:
    gbooks [options] [list] <q>


Options:
  -q, --quiet   Quiet operations
  -s, --strict  Strict operations
  -S --secret CLIENT_SECRET_FILE
                JSON formatted credentials.

"""
from __future__ import print_function
import httplib2
import os
from pprint import pprint, pformat

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

from script_mpe import libcmd_docopt
import confparse


#import argparse
#flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
#print 'flags', pformat(flags)
flags = confparse.Values(dict(
        logging_level= 'INFO',
        auth_host_port= [ 8080, 8090 ],
        auth_host_name= 'localhost',
        noauth_local_webserver= False
    ))


SCOPES = 'https://www.googleapis.com/auth/books'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Script.mpe - GBooks'
CRED_FILE = os.path.expanduser('~/.credentials/script-books.json')


def get_credentials(app_name, secret_file, credential_path, scopes):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(secret_file, scopes)
        flow.user_agent = app_name
        #credentials = tools.run(flow, store)
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials

def kwargs(*args):
    kwds = dict([ k.split('=') for k in args ])
    for k,v in kwds.items():
        if v.isdigit():
            kwds[k] = int(v)
    return kwds




## Sub-cmd handlers

def H_list(service, opts):
    r = service.volumes().list(q=opts.args.q).execute()
    print('Books for "%s"' % opts.args.q, len(r['items']))
    #print r.keys()

    for i in r['items']:
        v = confparse.Values(i)
        vi = v.volumeInfo

        #print i.keys()
        #print vi.keys()

        if 'subtitle' in vi:
            print(v.id, vi.publisher, vi.title, vi.subtitle, \
                vi.publishedDate, vi.language)
        else:
            print(v.id, vi.publisher, vi.title, \
                vi.publishedDate, vi.language)




handlers = {}
for k, h in locals().items():
    if not k.startswith('H_'):
        continue
    handlers[k[2:].replace('_', '-')] = h


def main(func=None, opts=None):
    """Shows basic usage of the Google Books API.
    """
    credentials = get_credentials(APPLICATION_NAME, opts.flags.secret,
            CRED_FILE, SCOPES)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('books', 'v1', http=http)

    return handlers[func](service, opts)



if __name__ == '__main__':
    import sys
    opts = libcmd_docopt.get_opts(__doc__)
    if not opts.cmds:
        opts.cmds = ['list']
    if not opts.flags.secret:
        if 'GOOGLE_SCRIPT_JSON_SECRET_FILE' in os.environ:
            opts.flags.secret = os.environ['GOOGLE_SCRIPT_JSON_SECRET_FILE']
        else:
            opts.flags.secret = CLIENT_SECRET_FILE
    sys.exit( main( opts.cmds[0], opts ) )
