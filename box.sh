#!/usr/bin/env make.sh
# Box - create namespaced script commands
# Id: script-mpe/0.0.4-dev box.sh
version=0.0.4-dev # script-mpe

set -eu

# Script subcmd's funcs and vars

box_man_1__stat="Stat local host script file"
box_spc__stat="-S|stat"
box_als___S=stat
box__stat()
{
  test -z "$dry_run" || note " ** DRY-RUN ** " 0
  test -n "$box_file" || error "no box for '$box_name'" 1

  $box_file status

  return $?

#  FIXME: this is more like a info list. need something more actual for stat. think about keeping state in files.."

  local_file=$BOX_DIR/$(hostname -s | tr 'A-Z' 'a-z')/${nid_cwd}.sh

  test -n "$local_file" && {
    subcmd_func_pref=c_$(hostname -s | tr 'A-Z' 'a-z')__ choice_all=1 \
      std__commands $local_file
  } || {
    error "No local file" 1
  }
}


box_man_1__edit="Edit localscript and box script or abort. "
box_spc__edit="-e|edit [<name>:]<script>"
box__edit()
{
  local c=0 script_files= \
    local_script= named_script= uconf_script=
  box_init_args $@
  test $c -eq 0 || shift $c ; c=0
  box_init_local || { r=$?
    test $r -eq 0 || error "$r error during box-init-local" $r
  }
  test -n "$choice_global" && {
    func_name=$global_func_name scope=global
    files="$fn $BOX_DIR/bin/${script_name} $script_files"
    note "Using **global** scope"
  } || {
    func_name=$local_func_name scope=local
    files="$script_files $BOX_DIR/bin/${script_name} $fn"
  }
  local evoke="$EDITOR" lib_files="$(eval echo $(dry_run= box_list_libs \
      $named_script $script_name | cut -d ' ' -f 4))"
  test "$EDITOR" = "vim" && {
    # Two vertical panes, with h-split in the right,
    # And execute search in first two.
    evoke="$EDITOR -O2 +/${nid_cwd} \
      -c "'":wincmd l"'" \
      -c :sp +/${nid_cwd} \
      -c "'"wincmd j"'" \
      -c :bn \
      -c "'"wincmd h"'
  }

  test -z "$dry_run" || {
    debug "files='$files'"
    debug "evoke='$evoke'"
    std_info "** DRY RUN ends **" 0
  }
  note "starting '$EDITOR' for $scope files of $box_name/$subbox_name"
  note "invoking '$evoke'"
  eval $evoke $files $lib_files
}
box_als___e="edit"


box_man_1__edit_main="Edit box script and local scripts. "
box_spc__edit_main="-E|edit-main"
box__edit_main()
{
  local c=0 script_files= \
    local_script= named_script= uconf_script=
  box_init_args $@
  test $c -eq 0 || shift $c ; c=0
  box_init_local || { r=$?
    test $r -eq 0 || error "$r error during box-init-local" $r
  }
  local files="$fn $script_files"
  local evoke="$EDITOR -O2"
  test -z "$dry_run" || {
    debug "files='$files'"
    debug "evoke='$evoke'"
    std_info "** DRY RUN ends **" 0
  }
  note "starting '$EDITOR' for $files"
  note "invoking '$evoke'"
  $evoke $files
}
box_als___E=edit-main


# FIXME: expect this is broken
box_als___i=init
box_man_1__init="Add script function, optionally providing command and script name"
box_spc__init='-i|init [<cmd>=run [<name>=$hostname]]'
box__init()
{
  local c=0 script_name= subcmd= \
    global_func_name= local_func_name= \
    local_script= named_script= uconf_script=

  box_init_args $@
  test $c -eq 0 || shift $c ; c=0
  box_init_local 2 || error "error during box-init-local" $?

  script_subcmd_func=$(echo $script_subcmd_name | tr '/-' '__')
  global_func_name=c_${script_name}__${script_subcmd_func}
  local_func_name=c_${script_name}__local__${nid_cwd}__${script_subcmd_func}

  test -z "$dry_run" || {
    debug "script_subcmd_func=$script_subcmd_func"
    debug "global_func_name='$global_func_name'"
    debug "local_func_name='$local_func_name'"
    std_info "** DRY RUN ends **" 0
  }

  error "FIXME" 1

  ## Init global function if needed
  grep -s '^'$global_func_name'()$' $named_script > /dev/null && {

    where_grep='.*#.--.'${script_name}'.box.include.main*--'
    file_insert_where_before $where_grep $named_script "$(cat <<-EOF
  . \$BOX_BIN_DIR/${script_name}/${nid_cwd}.sh
EOF
)"

    where_grep='.*#.--.'${script_name}'.box.'${subcmd}'.insert.*--'
    #box_sentinel_indent $where_grep $named_script
    file_insert_where_before $where_grep $named_script "$(cat <<-EOF
  # insert $script_name $subcmd by $base: $(datetime)
  box_run_cwd $(cwd) ${script_subcmd_func} ${subcmd_func_pref}${script_name}__local__
EOF
)"

  } || {

    line_number=$(box_script_insert_point $named_script)
    box_add_function $global_func_name $named_script:$line_number "$(cat <<-EOF
  set -- # no-op
  # $local_func_name
  # -- ${script_name} box ${subcmd} insert sentinel --
EOF
)
"
    note "Initialized function $global_func_name $named_script"
  }

  ## Init local function if needed
  # dont add it if exists in local script
  grep -s $nid_cwd'__'$cmd'()$' $named_script > /dev/null && {

    error "local function $cmd already exists in named_script $named_script" 1
  }

  # and dont add if exists in script
  { test -e "$local_script" &&
    grep -s $nid_cwd'__'$cmd'()$' $local_script > /dev/null; } && {

    error "function already exists in $local_script: $nid_cwd" 1
  }

  # add new to named script, ie dont create all loos scripts
  line_number=$(box_script_insert_point $named_script)
  box_add_function $local_func_name $named_script:$line_number "$(cat <<-EOF
  set -- # no-op
EOF
)"

  test -n "$script_name" \
      && log "Extended $script_name with script $nid_cwd $subcmd" \
      || log "Created local script $nid_cwd $subcmd"

  local files="$named_script $local_script $uconf_script"
  # XXX: vim only stuff
  local evoke="$EDITOR -O2 +/${nid_cwd}"
  note "invoking '$evoke'"
  $evoke $files
}


# FIXME new script

box__main_1_new="Initialize new localscript"
box_spc__new='-n|new [<name>=$hostname]'
box_als___n=new
box__new()
{
  local name= cmd=run c=0 script=
  box_name_args $@
  test $c -eq 0 || shift $c ; c=0
  local script=$BOX_BIN_DIR/$name
  test -e $script || box_init_script $script
  local func="${nid_cwd}_${name}_${cmd}"
  test -z "$dry_run" || {
    debug "script='$script'"
    debug "func='$func'"
    std_info "** DRY RUN ends **" 0
  }
  note "TODO check for existing function"
  box_add_function $func $script "$(cat <<-EOF
  set -- # no-op
  #echo This is $func in $script
EOF
)"
  mkvid c_${name}_${cmd}
  note "TODO add invocation to script function"
  #box_add_idx $vid $script $func
}


box__main_1_function="Initialize function for current location"
box_spc__function='-n|function [[<name>=$hostname] <cmd>=run]'
box__function()
{
  local name= cmd=run c=0
  upper=0 default_env scope "box"
  upper=0 default_env action "insert"
  box_name_args $@
  test -e $script || error "script $name does not exist" 1
  echo TODO add function to script
  echo "# -- $base $scope $action sentinel"
}
box_als___f=function


box_man_1__list="."
box_spc__list="list <Name>"
box__list()
{
  test -z "$dry_run" || {
    debug "nid_cwd='$nid_cwd'"
    debug "'$BOX_BIN_DIR/*'"
    std_info "** DRY RUN ends **" 0
  }
  std_info "TODO box list: get script names for local box command"
  grep -srI ${nid_cwd} $BOX_BIN_DIR/*
}
box_als___l=list


box_man_1__list_libs="List includes for script."
box_spc__list_libs="list-libs"
box__list_libs()
{
  local c=0 script_files= \
    local_script= named_script= uconf_script=
  box_init_args $@
  test $c -eq 0 || shift $c ; c=0
  box_init_local || { r=$?
    test $r -eq 0 || error "$r error during box-init-local" $r
  }

  box_list_libs $named_script $script_name
}

vs1_init_args_run()
{
  # XXX swap script-name with script-subcmd-name arg if latter is empty.. # always?
  if test -n "$script_name" -a -z "$script_subcmd_name"
  then
    script_subcmd_name=$script_name
    script_name=
  fi
  if test -z "$script_name"
  then
    script_name=$base
  fi
}

box_man_1__run="Run local or global function.

For local, require localscript and exec. given function.
"
box_spc__run='-r|run [<cmd>=run [<name>=$hostname]]'
box__run()
{
  local c=0 \
    global_func_name= local_func_name= \
    local_script= named_script= uconf_script=

  test -n "$script_name" || script_name=${base}
  named_script=$PREFIX/bin/box
  local_script=$BOX_DIR/$(hostname -s | tr 'A-Z' 'a-z')/${nid_cwd}.sh

  #box_init_args $@
  test $c -eq 0 || shift $c ; c=0
  test -n "$script_subcmd_name" || script_subcmd_name=$subcmd
  box_init_local || { r=$?
    test $r -eq 0 || error "$r error during box-init-local" $r
  }
  script_subcmd_func=$(echo $script_subcmd_name | tr '/-' '__')
  global_func_name=c_${script_name}__${script_subcmd_func}
  local_func_name=c_${script_name}__local__${nid_cwd}__${script_subcmd_func}

  test -n "$choice_global" && {
    func_name=$global_func_name scope=global
    note "Using **global** scope"
  } || {
    func_name=$local_func_name scope=local
  }

  test -z "$dry_run" || {
    debug "box_name=$box_name"
    debug "subbox_name=$subbox_name"
    debug "func_name=$func_name"
    debug "scope=$scope"
    debug "box_src=$box_src box_lib=$box_lib"
    std_info "** DRY RUN ends **" 0
  }

  # test for function
  type $func_name 2> /dev/null 1> /dev/null || {
    r=$?
    error "no $scope command $subbox_name"
    return $r
  }

  # run function
  $func_name $@ && {
    test -n "$choice_global" && {
      std_info "command $subbox_name completed"
    } || {
      std_info "command $subbox_name in $(pwd) completed"
    }
  } || {
    r=$?
    error "running $scope command $box_name"
    return $r
  }
}


box_man_1__="Default: (local) run"
box_als___c=run



box_man_1__complete="Testing bash complete with sh compatible script."
box_spc__complete=complete
box__complete()
{
  cmds=""
}


box_man_1__check_install="Run internal tests."
box_spc__check_install=check-install
box__check_install()
{
  {
    test -d "$BOX_DIR/" || error "not a dir" 1
    test -w "$BOX_DIR/" || error "not writable" 1
    test -d "$BOX_BIN_DIR/" || error "not a dir" 1
    test -x "$BOX_BIN_DIR/" || error "not accessible" 1
    box new BoxTest || error "unable to init BoxTest"
    std_info "initialized BoxTest"
    test "$(which BoxTest)" = "$BOX_BIN_DIR/BoxTest" \
      || error "expected BoxTest on PATH"
    BoxTest || error "unable to run BoxTest" 1
    rm $BOX_BIN_DIR/BoxTest

  } && {

    std_demo
    std_info "install checks OK"

  } || {
    rm -vf $BOX_BIN_DIR/BoxTest
    return 1
  }
}

# TEST: box 

box__log_demo()
{
  debug "Debug msg"
  std_info "Info msg"
  note "Notice msg"
  warn "Warning msg"
  error "Error msg"
  #emerg "Emergency msg"
  crit "Critical msg"
}


box_man_1__d='Query, or start instance in/to background

Starts a new box.py, or queries an existing instance via Unix domain
socket. With no arguments request an instance to run at pd_sock, to be
backgrounded as helper for script. A simple line protocol is used, the
quoted command arguments are passed in as line, and some simple str glob
patterns are used to return/output various result states. '
box__d()
{
  test -n "$1" || set -- --background
  fnmatch "$1" "-*" || {
    test -x "$(which socat)" -a -e "$box_sock" && {

      main_sock=$box_sock main_bg_writeread "$@"
      return $?
    }
  }
  test -n "$box_sock" && set -- --address $box_sock "$@"
  $scriptpath/box.py "$@" || return $?
}


box__specs()
{
  htd functions list "$@" | box__d specs -
}


box_man_1__context='
'
box__context()
{
  subcmd_default=list subcmd_prefs=${base}_context_\ htd_context_\ context_ try_subcmd_prefixes "$@"
}

box_flags__context=l
box_libs__context=statusdir\ statusdir-uc\ sys-uc\ context\ context-uc\ htd-context


box_man_1__cwd='
  list
  exists
  init
'
box__cwd()
{
  local boxtab=$BOX_DIR/$hostname.list
  subcmd_default=list subcmd_prefs=${base}_cwd_ try_subcmd_prefixes "$@"
}

box_cwd_list()
{
  box_cwds_tab_assert || return
  test $# -eq 0 || return 3
  read_nix_style_file $boxtab
}

box_cwd_exists()
{
  box_cwds_tab_assert || return
  test -n "$*" || set -- "$PWD"
  test $# -eq 1 || return 3
  grep -qF "$1" "$boxtab"
}

box_cwd_init()
{
  test -n "$*" || set -- "$PWD"
  test $# -eq 1 || return 3
  box_cwd_exists "$@" && {
    error "Cannot create entry exists" 1
  }
  test -e $1/load.sh -o -e $1/load.$SHELL_NAME || return 2
  # XXX: lots of auto-detect potential for cwds here with hooked
  # handles:
  #test -e package.sh
  #test -e package.yml -o -e package.yaml
  #test -e package.json
  echo "$1" | tee -a $boxtab
}

box_cwds_tab_assert()
{
  test -e $boxtab || warn "No initialized cwds" 20
}


# -- box box insert sentinel --



# Generic subcmd's

# TODO: get a proper opt parser and do something like this:
box_man_1__help="Box: Generic: Help

  -h|help [<id>]      Print usage info, abbreviated command list and documentation
                      reference. Use 'help help', 'docs' or 'help docs' for
                      extended output. "
box__help()
{
  choice_global=1 std__help $*
}
# XXX compile these from human readable cl-option docstring, provide bash
#   auto-completion. Need to work out man5 and man7 stuff still. Save lot of
#   clutter.
box_man_1__help="Echo a combined usage, commands and docs"
box_spc__help="-h|help [<id>]"
box_als___h="help"


box_man_1__commands="List all commands"
box__commands()
{
  choice_global=1 std__commands
}
box_als___c=commands


search="htd\ box\ insert\ sentinel"


box__type()
{ true
}


box__here()
{ true
}


# Script main parts

main_env \
  INIT_ENV="init-log strict 0 0-src 0-u_s dev ucache scriptpath std box" \\
  INIT_LIB="\$default_lib str-htd logger-theme main box src-htd"
main_local \\
  box_sock= box_lib=
main_init box_sock=/tmp/box-serv.sock
main-lib box_lib_current_path
main-load box_name="${base}:${subcmd}" \
  sh_include_path_langs="htd main ci bash sh"
main-load-flags \
    l ) sh_include subcommand-libs || return ;; \
    f ) # failed: set/cleanup failed varname \
        export failed=$(setup_tmpf .failed) \
      ;; \
      \
    * ) error "No load flag <$x>" 3 ;; \

main_unload unset box_name \
  sh_include_path_langs="htd main ci bash sh"
main_unload_flags \
    l ) ;; \
    * ) error "No unload flag <$x>" 3 ;; \

main_load_epilogue \
# Id: script-mpe/0.0.4-dev box.sh                                  ex:ft=bash:
