#!/usr/bin/env python
__version__ = '0.0.0'
__db__ = 'postgresql+psycopg2://redmine:password@localhost:15432/redmine_production'
__usage__ = """
redmine-meta - Read data from Redmine database.

Usage:
    rdm [options] issues
    rdm [options] projects
    rdm [options] custom-fields
    rdm [options] print-db-ref

Options:
    -v            Increase verbosity.
    -d REF --dbref=REF
                  SQLAlchemy DB URL [default: %s].
    -y --yes
    -V, --version  Show version (%s).

Dependencies:
  psycopg2
    postgresql-devel (Debian: libpq-dev)
      ..

""" % ( __db__, __version__ )
from script_mpe import util, log
from script_mpe import redmine_schema as rdm
from script_mpe.redmine_schema import get_session




### Program sub-commands


def cmd_projects(settings):

    """
        List projects, with id and parent id.
    """

    sa = get_session(settings.dbref)
    l = 'Projects'
    v = sa.query(rdm.Project).count()
    # TODO: filter project; age, public
    log.info('{green}%s{default}: {bwhite}%s{default}', l, v)
    print '# ID PARENT NAME'
    for p in sa.query(rdm.Project).all():
        print p.id, p.parent_id or '-', p.name


def cmd_issues(settings):

    """
        List issues
    """

    sa = get_session(settings.dbref)
    l = 'Issues'
    # TODO: filter issues; where not closed, where due, started, etc.
    v = sa.query(rdm.Issue).count()
    log.info('{green}%s{default}: {bwhite}%s{default}', l, v)
    print('# ID PARENT_ID ROOT_ID SUBJECT ')
    #print('# ID PARENT_ID ROOT_ID PRIO SUBJECT ')
    for i in sa.query(rdm.Issue).all():
        print i.id,
        for k in i.parent_id, i.root_id:
            print k or '-',
        #print i.priority_id or '-', i.subject
        print i.subject


def cmd_custom_fields(settings):

    """
        List custom-fields
    """

    sa = get_session(settings.dbref)
    l = 'Custom Fields'
    # TODO: filter custom_fields;
    v = sa.query(rdm.CustomField).count()
    log.info('{green}%s{default}: {bwhite}%s{default}', l, v)
    for rs in sa.query(rdm.CustomField).all():
        print rs.id, rs.type
        print "  Name:", rs.name
        if rs.possible_values: # yaml value
            print "  Possible values: "
            for x in rs.possible_values.split('\n'):
                if x == '---': continue
                print "  ",x
        if rs.description:
            print "  Description:"
            print "   ", rs.description.replace('\n', '\n    ')

def cmd_print_db_ref(settings):
    print settings.dbref



### Transform cmd_ function names to nested dict

commands = util.get_cmd_handlers_2(globals(), 'cmd_')



### Util functions to run above functions from cmdline

def main(opts):

    """
    Execute command.
    """

    settings = opts.flags
    opts.default = ['info']
    return util.run_commands(commands, settings, opts)

def get_version():
    return 'redmine-meta.mpe/%s' % __version__

argument_handlers = {
}

if __name__ == '__main__':

    import sys
    opts = util.get_opts(__usage__, meta=argument_handlers, version=get_version())
    opts.flags.dbref = opts.flags.dbref
    sys.exit(main(opts))

