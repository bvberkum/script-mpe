#!/bin/sh
ino__source=$_

# Using Arduino (on Darwin)

set -e

version=0.0.0+20150911-0659 # script.mpe



ino__man_1_help="Echo a combined usage and command list. With argument, seek all sections for that ID. "
ino__spc_help='-h|help [ID]'
ino__help()
{
  choice_global=1 std_help ino "$@"
}
ino__als__h=help


ino__als__V=version
ino__man_1_version="Version info"
ino__spc_version="-V|version"
ino__version()
{
  echo "$(cat $PREFIX/bin/.app-id)/$version"
  app_version=$( basename $(readlink $APP_DIR/Arduino.app) | \
    sed 's/.*Arduino-\([0-9\.]*\).app/\1/' )
  echo "Arduino/$app_version"
}


ino__man_1_edit="Edit the main script file"
ino__spc_edit="-E|edit-main"
ino__edit()
{
  locate_name $scriptname || exit "Cannot find $scriptname"
  note "Invoking $EDITOR $fn"
  $EDITOR $fn "$@" nodes.tab
}
ino__als__e=edit


ino__man_1_list_ino="List Arduino versions available in APP_DIR"
ino__list_ino()
{
  for path in $APP_DIR/Arduino-*
  do
    basename $path .app \
      | sed 's/^.*Arduino-\([0-9\.]*\)/\1/'
  done
}


ino__man_1_switch="Switch to Arduino version"
ino__switch()
{
  test -n "$1" || err "expected version arg" 1
  cd $APP_DIR || err "cannot change to $APP_DIR" 1
  test -e Arduino-$1.app || err "no version $1" 1
  test -h Arduino.app || err "not a symlink $APP_DIR/Arduino.app" 1
  rm Arduino.app || err "unable to remove symlink $APP_DIR/Arduino.app" 1
  ln -s Arduino-$1.app Arduino.app
}


ino__man_1_list="List sketches"
ino__list()
{
  list_mk_targets Rules.old.mk
}

# list (static) targets in makefile
list_mk_targets()
{
  grep -h '^[a-z0-9]*: [^=]*$' $1 \
    | sed 's/:.*$//' | sort -u | column
}

node_tab=nodes.tab

get_nodes()
{
  fixed_table_hd $node_tab ID PREFIX CORE BOARD DEFINES
}

# Build/upload image for arg1:nodeid
ino__build()
{
  test -z "$2" || error "surplus args" 1
  get_nodes | while read vars
  do
    eval local "$vars"
    test "$ID" = "$1" || continue
    make build INO_PREF=$PREFIX C=$CORE BRD=$BOARD DEFINES="$DEFINES"
  done
}


ino__list_prototype_parts()
{
  ino__list_sketches Prototype Mpe | sort -u \
    | {
      while read ino
      do
        grep '^\/\*\ \*\*\*\ .*\*\*\*\ {{' $ino | \
          sed 's/[^A-Za-z0-9\ ]//g'
      done
    } | sort -u
}

get_sketch()
{
  sketchname=$(basename $1)
  test ! -e "$1/$sketchname.ino" || {
    echo $1/$sketchname.ino
  }
  test ! -e "$1/$sketchname.pde" || {
    echo $1/$sketchname.pde
  }
}

# XXX: this misses deeper sketchs..
ino__list_sketches()
{
  test -n "$1" || set -- Mpe Prototype
  while test $# -gt 0
  do
    for path in $1/*
    do
      find $path -iname '*.ino' -o -iname '*.pde'
      #ino=$(get_sketch $path)
      #test -n "$ino" -a -e "$ino" && {
      #  echo $ino
      #} || {
      #  warn "No sketch in $path"
      #}
    done
    shift
  done
}

### Main


ino_main()
{
  ino_init || return 0

  local scriptname=ino base=$(basename $0 .sh) verbosity=5

  case "$base" in $scriptname )

      local subcmd_def= \
        subcmd_pref= subcmd_suf= \
        subcmd_func_pref=${base}__ subcmd_func_suf=

      ino_lib

      # Execute
      run_subcmd "$@"
      ;;

  esac
}

ino_init()
{
  test -n "$PREFIX" || PREFIX=$HOME
  test -z "$BOX_INIT" || return 1
  . $PREFIX/bin/box.init.sh
  . $PREFIX/bin/util.sh
  box_run_sh_test
  . $PREFIX/bin/main.sh
  . $PREFIX/bin/main.init.sh
  . $PREFIX/bin/box.lib.sh
  . $PREFIX/bin/htd
}

ino_lib()
{
  # -- ino box lib sentinel --
  set --
}

ino_load()
{
  test -n "$UCONFDIR" || UCONFDIR=$HOME/.conf/
  test -n "$INO_CONF" || INO_CONF=$UCONFDIR/ino
  test -n "$APP_DIR" || APP_DIR=/Applications

  hostname="$(hostname -s | tr 'A-Z.-' 'a-z__' | tr -s '_' '_' )"

  test -n "$EDITOR" || EDITOR=vim
  # -- ino box load sentinel --
  set --
}

# Use hyphen to ignore source exec in login shell
if [ -n "$0" ] && [ $0 != "-bash" ]; then
  ino_main "$@"
fi

