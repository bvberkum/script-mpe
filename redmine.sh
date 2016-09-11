#!/bin/sh

redmine_src=$_
test -z "$__load_lib" || set -- "load-ext"

set -e



redmine__projects()
{
  local remote_host=dandy remote_user=hari
  on_host $remote_host || ssh_req $remote_host $remote_user
  local projects=$(setup_tmpf -projects.tab)

  run_cmd "$remote_host" "redmine_meta.py projects" > $projects
  cat $projects | sed -E 's/([0-9]+\ )+//g'
  note "$(count_lines $projects) projects at RDM $remote_host"
}

redmine__list()
{
  redmine__issues
}

redmine__issues()
{
  local remote_host=dandy remote_user=hari
  on_host $remote_host || ssh_req $remote_host $remote_user
  local issues=$(setup_tmpf -issues.tab)

  run_cmd "$remote_host" "redmine_meta.py issues" > $issues
  cat $issues | sed -E 's/([0-9-]+\ )+//g'
  note "$(count_lines $issues) issues at RDM $remote_host"
}



### Main


redmine_main()
{
  local scriptname=redmine base=$(basename $0 .sh) verbosity=5 \
    scriptdir="$(cd "$(dirname "$0")"; pwd -P)" \
    failed=

  redmine_init || exit $?

  case "$base" in

    $scriptname )

        test -n "$1" || set -- list

        redmine_lib || exit $?
        run_subcmd "$@" || exit $?
      ;;

    * )
        error "not a frontend for $base ($scriptname)" 1
      ;;

  esac
}

redmine_init()
{
  # XXX test -n "$SCRIPTPATH" , does $0 in init.sh alway work?
  test -n "$scriptdir"
  export SCRIPTPATH=$scriptdir
  . $scriptdir/util.sh
  util_init
  . $scriptdir/match.lib.sh
  . $scriptdir/box.init.sh
  box_run_sh_test
  #. $scriptdir/htd.lib.sh
  . $scriptdir/main.lib.sh
  . $scriptdir/main.init.sh
  . $scriptdir/meta.lib.sh
  . $scriptdir/box.lib.sh
  . $scriptdir/date.lib.sh
  . $scriptdir/doc.lib.sh
  . $scriptdir/table.lib.sh
  lib_load remote
  # -- redmine box init sentinel --
}

redmine_lib()
{
  local __load_lib=1
  . $scriptdir/match.sh load-ext
  # -- redmine box lib sentinel --
  set --
}

redmine_load()
{
  test -n "$hostname" || hostname="$(hostname -s | tr 'A-Z' 'a-z')"
}


# Use hyphen to ignore source exec in login shell
case "$0" in "" ) ;; "-"* ) ;; * )
  # Ignore 'load-ext' sub-command
  test -z "$__load_lib" || set -- "load-ext"
  case "$1" in load-ext ) ;; * )
    redmine_main "$@"
  ;; esac
;; esac


