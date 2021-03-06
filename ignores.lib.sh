#!/bin/sh

ignores_lib_load()
{
  test -n "$1" || set -- $base
  test -n "$2" || set -- $1 $(str_upper $1)

  test -n "$SCRIPT_ETC" -a -e "$SCRIPT_ETC" || error "SCRIPT-ETC '$SCRIPT_ETC'" 2

  local varname=$(echo $2 | tr '-' '_')_IGNORE fname=.${1}ignore

  export IGNORE_GLOBFILE_VAR=$varname
  export IGNORE_GLOBFILE=$(eval echo \"\$$IGNORE_GLOBFILE_VAR\")
  test -z "$DEBUG" || {
    test -n "$IGNORE_GLOBFILE" || warn "No IGNORE_GLOBFILE for $varname set"
  }

  test -n "$(eval echo \"\$$varname\")" || eval $varname=$fname
  local value="$(eval echo "\$$varname")"

  test -e "$value" || {
    value=$(setup_tmpf $fname)
    eval $varname=$value
    touch $value
  }
  export $varname
}

ignores_group_names()
{
  echo local global
  echo purge clean drop
  echo tracked ignored untracked
}

# TODO: extendable/customizable groups (list file paths)
ignores_groups()
{
  while test -n "$1"
  do
    case "$1" in
      purge ) set -- "$@" local-purge global-purge ;;
      clean ) set -- "$@" local-clean global-clean ;;
      drop ) set -- "$@"  local-drop global-drop ;;

      ignore ) echo ".ignored" ;;

      local ) set -- "$@" local-clean local-purge local-drop ;;
      local-clean )
          echo $IGNORE_GLOBFILE-cleanable
          echo $IGNORE_GLOBFILE-clean
        ;;
      local-drop )
          echo $IGNORE_GLOBFILE-droppable
          echo $IGNORE_GLOBFILE-drop
        ;;
      local-purge )
          echo $IGNORE_GLOBFILE-purgeable
          echo $IGNORE_GLOBFILE-purge
        ;;

      global ) set -- "$@" global-clean global-purge global-drop ;;
      global-clean ) echo etc:cleanable.globs ;;
      global-purge ) echo etc:purgeable.globs ;;
      global-drop ) echo etc:droppable.globs ;;

      scm ) set -- "$@" scm-git scm-bzr scm-svn ;;
      scm-git )
          echo .gitignore
          echo .git/info/exclude
          # TODO: .attributes see pd:list-paths opts parsing;
        ;;
      scm-svn ) ;;
      scm-hg ) ;;
      scm-bzr )
          echo .bzrignore
        ;;
      * ) error "Unhandled ignores-group '$*'" 1 ;;
    esac
    shift
  done | sort -u
}

ignores_groups_exist()
{
  set -- $(ignores_groups "$@" | lines_to_words ) # Remove options, resolve args
  note "Resolved ignores to '$*'"

  while test -n "$1"
  do
    case "$1" in

      etc:* )
            test -e \
              "$SCRIPT_ETC/htd/list-ignores/$(echo "$1" | cut -c5-)" || {
                  shift; continue; }
          ;;

      * )
            test -e "$1" || { shift; continue; }
          ;;

    esac
    echo "$1"
    shift
  done
}

# Convenient access to glob lists (cat files)
ignores_cat()
{
  local src_a="$*"
  set -- $(ignores_groups "$@" | lines_to_words ) # Remove options, resolve args
  note "Resolved ignores source '$src_a' to files '$*'"

  while test -n "$1"
  do
    case "$1" in

      etc:* )
          read_if_exists \
            "$SCRIPT_ETC/htd/list-ignores/$(echo "$1" | cut -c5-)" ||
              note "Nothing to read for '$1'" ;;

      * )
          read_if_exists "$1" ;;

    esac
    shift
  done
}

glob_to_find_prune()
{
  # Filter matches on name
  echo $(echo "$1" | \
    grep -Ev '^(#.*|\s*)$' | \
    sed -E 's/^\//\.\//' | \
    grep -v '\/' | \
    sed -E 's/(.*)/ -o -name "\1" -prune /g')
  # Filter matches on other paths
  echo $(echo "$1" | \
    grep -Ev '^(#.*|\s*)$' | \
    sed -E 's/^\//\.\//' | \
    grep '\/' | \
    sed -E 's/(.*)/ -o -path "*\1*" -prune /g')
}

# Return find ignore flags for given exclude pattern file
find_ignores()
{
  for a in $@
  do
    # Translate gitignore lines to find flags
    read_nix_style_file $a | while read glob
      do glob_to_find_prune "$glob"; done
  done | grep -Ev '^(#.*|\s*)$'
}
