import os, sys
import re

from fnmatch import fnmatch
from res import js
from confparse import yaml_load, yaml_safe_dump


re_non_escaped = re.compile('[\[\]\$%:<>;|\ ]')
re_alphanum = re.compile('[^a-z0-9A-Z]')

class AbstractKVParser(object):

    """
    Parse dict or list from arguments::

        a/b/c=1 a/d=2  ->  { a: { b: { c: 1 }, d: 2 } }

    """

    def __init__(self, seed=None, rootkey=None):
        super(AbstractKVParser, self).__init__()
        self.data = seed
        if rootkey:
            self.scan_root_type(rootkey)

    def scan_root_type(self, key):
        "Initialize root (self.data) to correct data type: dict or list"
        if '/' in key:
            key = key.split('/')[0]
        self.data = FlatKVParser.get_data_instance(key)

    def scan(self, fh):
        " Parse from file, listing one kv each line. "

        # XXX: need bufered read..
        pos = fh.tell()
        if self.data is None:
            rootkey = fh.read(1)
            while rootkey[-1] != '=':
                rootkey += fh.read(1)
            self.scan_root_type(rootkey)
            fh.seek(pos)

        for line in fh.readlines():
            self.set_kv(line)

    def scan_kv_args(self, args):
        " Parse from list of kv's. "
        for arg in args:
            self.set_kv(arg)

    def set_kv(self, kv):
        " Split kv to key and value, the the first '=' occurence. "
        if '=' not in kv: return
        pos = kv.index('=')
        key, value = kv[:pos].strip(), kv[pos+1:].strip()
        self.set( key, value )


    def set( self, key, value, d=None, default=None ):
        """ Parse key to path within dict/list struct and insert value.
        kv syntax::

            list[] = value
            key = value
            key/sub = value

        Append value to a list::

            key/list[5]/subkey/mylist[] = value

        """
        if isinstance(value, basestring) and value.isdigit():
            value = int(value)
        if d is None:
            d = self.data
        if '/' in key:
            self.set_path(key.split('/'), value)
        else:
            di = self.__class__.get_data_instance(key)
            if isinstance(di, list):
                pos = key.index('[')
                if key[:pos] not in d:
                    d[key[:pos]] = di
                if len(key) > pos+2:
                    idx = int(key[pos:-1])
                    d[key[:pos]][idx] = value
                else:
                    d[key[:pos]].append( value )
                return key[:pos]
            else:
                if value is None and default is not None:
                    if key not in d:
                        d[key] = default
                else:
                    d[key] = value
                return key

    def set_path( self, path, value ):
        assert isinstance(path, list), "Path must be a list"
        d = self.data
        while path:
            k = path.pop(0)
            di = self.__class__.get_data_instance(k)
            if path:
                k = self.set( k, None, d, di )
            else:
                k = self.set( k, value, d )
            if path:
                d = d[k]

    @staticmethod
    def get_data_instance(key):
        "Get data container instance based on key pattern"
        raise NotImplementedError
        return None


class PathKVParser(AbstractKVParser):

    @staticmethod
    def get_data_instance(key):
        if fnmatch(key, '*\[[0-9]\]') or fnmatch(key, '*[]'):
            return []
        else:
            return {}

class FlatKVParser(AbstractKVParser):

    @staticmethod
    def get_data_instance(key):
        if fnmatch(key, '*__[0-9]*') or fnmatch(key, '*__*'):
            return []
        else:
            return {}



class AbstractKVSerializer(object):

    itemfmt, dirfmt = None, None

    write_indices = True

    def serialize(self, data, prefix=''):
        if prefix is None:
            prefix = ''
        return os.linesep.join(self.ser(data, prefix))
    def ser(self, data, prefix=''):
        r = []
        if isinstance(data, list):
            r.extend(self.ser_list(data, prefix))
        elif isinstance(data, dict):
            r.extend(self.ser_dict(data, prefix))
        else:
            if re_non_escaped.search(data):
                r.append( "%s=\"%s\"" % ( prefix, data ))
            else:
                r.append( "%s=%s" % ( prefix, data ))
        return r
    def ser_list(self, data, prefix=''):
        r = []
        for i, item in enumerate(data):
            if not self.write_indices:
                i = ''
            r.extend(self.ser(item, prefix + self.itemfmt % i))
        return r
    def ser_dict(self, data, prefix=''):
        r = []
        for key, item in data.items():
            r.extend(self.ser(item, self.dir_prefix(prefix, key)))
        return r
    def dir_prefix(self, prefix, key):
        raise NotImplementedError

class PathKVSerializer(AbstractKVSerializer):
    dirfmt = '/%s'
    itemfmt = '[%s]'

    def dir_prefix(self, prefix, key):
        sp = prefix and prefix + self.dirfmt or '%s'
        return sp % key


class FlatKVSerializer(AbstractKVSerializer):
    dirfmt = '_%s'
    itemfmt = '__%s'

    def dir_prefix(self, prefix, key):
        sp = prefix and prefix + self.dirfmt or '%s'
        return sp % re_alphanum.sub('_', key)

def load_data(infmt, infile):
    return readers[ infmt ]( infile )

def stdout_data(outfmt, data, outfile, opts):
    writers[ outfmt ]( data, outfile, opts )



### Readers/Writers

def pkv_reader(file):
    reader = PathKVParser()
    reader.scan(file)
    return reader.data

def fkv_reader(file):
    reader = FlatKVParser()
    reader.scan(file)
    return reader.data

readers = dict(
        json=js.load,
        yaml=yaml_load,
        pkv=pkv_reader,
        fkv=fkv_reader
    )


def pkv_writer(data, file, opts):
    writer = PathKVSerializer()
    if opts.flags.no_indices:
        writer.write_indices = False
    file.write(writer.serialize(data))

def fkv_writer(data, file, opts):
    writer = FlatKVSerializer()
    if opts.flags.no_indices:
        writer.write_indices = False
    file.write(writer.serialize(data, opts.flags.output_prefix))

def json_writer(data, file, opts):
    kwds = {}
    if opts.flags.pretty:
        kwds.update(dict(indent=2))
    file.write(js.dumps(data, **kwds))
    print >> file

def yaml_writer(data, file, opts):
    kwds = {}
    if opts.flags.pretty:
        kwds.update(dict(default_flow_style=False))
    yaml_safe_dump(data, file, **kwds)

writers = dict(
        json=json_writer,
        yaml=yaml_writer,
        pkv=pkv_writer,
        fkv=fkv_writer
    )


### Misc. argument/option handling

def get_src_dest(opts):
    infile, outfile = None, None
    if opts.args.srcfile:
        if opts.args.srcfile == '-':
            infile = sys.stdin
        else:
            infile = open(opts.args.srcfile)
        if 'destfile' in opts.args and opts.args.destfile:
            if opts.args.destfile == '-':
                outfile = sys.stdout
            else:
                outfile = open(opts.args.destfile, 'w+')
    return infile, outfile

def set_format(tokey, fromkey, opts):
    file = getattr(opts.args, "%sfile" % fromkey)
    if file:
        fmt = get_format_for_fileext(file)
        if fmt:
            setattr(opts.flags, "%s_format" % tokey, fmt)

def get_format_for_fileext(fn):
    if fn.endswith('yaml') or fn.endswith('yml'):
        return 'yaml'

    if fn.endswith('json'):
        return 'json'

def get_src_dest_defaults(opts):

    if opts.flags.detect_format:
        set_format('input', 'src', opts)
        set_format('output', 'dest', opts)

    infile, outfile = get_src_dest(opts)
    if not outfile:
        outfile = sys.stdout
        if not infile:
            infile = sys.stdin
    return infile, outfile

