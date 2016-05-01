#!/usr/bin/env python
"""
Javascript Object toolkit.

Usage:
    jsotk [options] path <srcfile> <expr>
    jsotk [options] objectpath <srcfile> <expr>
    jsotk [options] [dump] [<srcfile> [<destfile]]
    jsotk [options] (json2yaml|yaml2json) [<srcfile> [<destfile>]]
    jsotk [options] (from-kv|to-kv) [<srcfile> [<destfile>]]
    jsotk [options] (from-flat-kv|to-flat-kv) [<srcfile> [<destfile>]]
    jsotk [options] from-args <kv_args>...
    jsotk [options] from-flat-args <fkv-args>...
    jsotk [options] merge-one <srcfile> <srcfile2> <destfile>
    jsotk [options] merge [<srcfiles>...] <destfile>
    jsotk [options] update <srcfile> [<destfile>]
    jsotk [options] update-from-args <srcfiles> <kv-args> <destfile>


Options:
  -q, --quiet   Quiet operations
  -s, --strict  Strict operations
  -p, --pretty  Pretty output formatting.
  -I <format>, --input-format <format>
                Override input format. See Formats_.
                TODO: default is to autodetect from filename
                if given, or set to [default: json].
  -O <format>, --output-format <format>
                Override output format. See Formats_.
                TODO: default is to autodetect from filename
                if given, or set to [default: json].
  --no-indices  [default: false]
  --detect-format
  --no-detect-format
                Auto-detect input/output format based on file-name extension
                [default: true]
  --output-prefix PREFIX
                Path prefix for output [default: ]
  --list-update
                .
  --list-update-nodict
                .
  --list-union
                .

Formats
-------
json
    ..
yaml
    ..
"""
import os, sys
import types

from docopt import docopt
from objectpath import Tree


import util
from jsotk_lib import PathKVParser, FlatKVParser, \
        load_data, stdout_data, readers, \
        get_src_dest_defaults, set_format, \
        deep_union, deep_update


### Sub-command handlers

# Conversions, json is default format

def H_dump(opts):
    "Read src and write destfile according to set i/o formats. "
    infile, outfile = get_src_dest_defaults(opts)
    data = load_data( opts.flags.input_format, infile )
    return stdout_data( opts.flags.output_format, data, outfile, opts )


def H_merge_one(opts):

    opts.args.srcfiles = [ opts.args.srcfile, opts.args.srcfile2 ]
    H_merge(opts)


def H_merge(opts):
    "Merge srcfiles into last file. All srcfiles must be same format. "
    "Defaults to src-to-dest noop, stdin/out: - -. "

    if not opts.args.srcfiles:
        opts.args.srcfile = '-'
        return H_dump(opts)
    else:
        opts.args.srcfile = opts.args.srcfiles[0]
        set_format('input', 'src', opts)

    if not (opts.flags.list_union or opts.flags.list_update):
        if opts.flags.list_update_nodict:
            opts.flags.list_update = True
        else:
            opts.flags.list_union = True

    data = None
    for srcfile in opts.args.srcfiles:
        infile = open(srcfile)
        mdata = load_data( opts.flags.input_format, infile )
        if not data:
            data = type(mdata)()
        elif not isinstance(mdata, type(data)):
            raise ValueError, "Srcsfiles must have same root type. "\
                    "Expected %s, but found %s (%s)" % (
                            type(data), type(mdata), srcfile )
        if isinstance(data, dict):
            deep_update([data, mdata], opts)
        elif isinstance(data, list):
            data = deep_union([data, mdata], opts)
        else:
            raise ValueError, data

    if opts.args.destfile == '-':
        outfile = sys.stdout
    else:
        outfile = open(opts.args.destfile, 'w+')
    return stdout_data( opts.flags.output_format, data, outfile, opts )

def H_update(opts):
    "Update srcfile from stdin. Write to destfile or stdout. "



# Ad-hoc designed path query

def H_path(opts):
    infile, outfile = get_src_dest_defaults(opts)
    l = load_data( opts.flags.input_format, infile )
    path_el = opts.args.expr.split('.')
    while len(path_el):
        b = path_el.pop(0)
        if b not in l:
            raise KeyError, b
        l = l[b]
    print l

def H_objectpath(opts):
    infile, outfile = get_src_dest_defaults(opts)
    q = Tree(load_data( opts.flags.input_format, infile ))
    o = q.execute( opts.args.expr )
    if isinstance(o, types.GeneratorType):
        for s in o:
            v = stdout_data( opts.flags.output_format, s, outfile, opts )
            if v:
                return v
    else:
        return stdout_data( opts.flags.output_format, o, outfile, opts )



# TODO: helper for plain text (parser-less) updates to YAML/JSON

def H_offsets(opts):
    """
    TODO: could print offsets from yaml.tokens.*.start/end_mark

    Print source offsets in line/column and absolute characters
    for
        --keys
        --list-items

    mloatk offsets --key redmine --list-items
    mloatk offsets --path redmine.image --value
    mloatk offsets --path redmine.image --value

    """


## Conversion shortcuts


def H_yaml2json(opts):
    opts.flags.input_format = 'yaml'
    return H_dump(opts)

def H_json2yaml(opts):
    opts.flags.output_format = 'yaml'
    return H_dump(opts)


# Flat key-value from/to nested list/dicts

def H_from_args(opts):
    args = opts.args.kv_args
    reader = PathKVParser(rootkey=args[0])
    reader.scan_kv_args(args)
    return stdout_data( opts.flags.output_format, reader.data, sys.stdout, opts )

def H_from_kv(opts):
    opts.flags.input_format = 'pkv'
    return H_dump(opts)

def H_to_kv(opts):
    opts.flags.output_format = 'pkv'
    return H_dump(opts)


def H_from_flat_args(opts):
    args = opts.args.fkv_args
    reader = FlatKVParser(rootkey=args[0])
    reader.scan_kv_args(args)
    return stdout_data( opts.flags.output_format, reader.data, sys.stdout, opts )

def H_from_flat_kv(opts):
    opts.flags.input_format = 'fkv'
    return H_dump(opts)

def H_to_flat_kv(opts):
    opts.flags.output_format = 'fkv'
    return H_dump(opts)



### Main


handlers = {}
for k, h in locals().items():
    if not k.startswith('H_'):
        continue
    handlers[k[2:].replace('_', '-')] = h


def main(func=None, opts=None):

    return handlers[func](opts)


if __name__ == '__main__':
    opts = util.get_opts(__doc__)
    if not opts.cmds:
        opts.cmds = ['dump']
    if opts.flags.no_detect_format:
        opts.flags.detect_format = False
    else:
        opts.flags.detect_format = True
    sys.exit( main( opts.cmds[0], opts ) )


