#!/bin/sh

# Scan for emmbedded tags and comments

set -e
scriptname=tools/sh/tags
test -n "$scriptpath" || scriptpath=$(dirname $(dirname $(dirname $0)))
test -n "$verbose" || verbose=true
test -n "$exit" || exit=true

lname=script-mpe

type lib_load 2> /dev/null 1> /dev/null || . $scriptpath/util.sh load-ext

lib_load sys os std str
out=$(setup_tmpf .out)

note "Embedded issues check.. ($(var2tags verbose exit))"

test -n "$Check_All_Files" || Check_All_Files=0
test -n "$Check_All_Tags" || Check_All_Tags=0

test -z "$1" && {
  trueish "$Check_All_Files" && {
    check_files="*"
  } || {
    # Only go over staged changes
    check_files="$(git diff --name-only --cached --diff-filter=ACMR)"
    test -n "$check_files" && {
      note "Set check-files to GIT modified files.."
    } || {
      note "Cant find modified files, setting to all files"
      check_files="*"
    }
  }
} || {
  check_files="$@"
}

# TODO: compile this regex
trueish "$Check_All_Tags" && {
  test -n "$abort_on_regex" || abort_on_regex='\<\(SCRIPT-MPE\|TODO\|FIXME\|XXX\)\>' # tasks:no-check
} || {
  test -n "$abort_on_regex" || abort_on_regex='\<XXX\>' # tasks:no-check
}

# TODO: should move exclude params into pd or lst, once handled ok
test -e .git && \
  src_grep="git grep -n" || src_grep="grep -nsrI \
    --exclude-dir 'build' \
    --exclude-dir jjb \
    --exclude-dir 'vendor' \
    --exclude '*.tmpl' \
    --exclude '*.sw[aop]' \
    --exclude '*~' \
    --exclude '*.lock' \
    --exclude '*.html' \
    --exclude 'TODO.list' \
    --exclude '.package.sh' \
    --exclude '.package.json' \
  "

$src_grep \
    $abort_on_regex \
    $check_files \
  | . ./tools/sh/tags-filter.sh \
	| \
  {
    trueish "$verbose" && { tee $out; } || { cat - > $out; }
  }

cruft=$(count_lines $out)

ret=0
test -n "$max" || max=0
tags="$(var2tags Check_All_Files Check_All_Tags check_files)"
test $max -ge $cruft && {
  test $max -eq 0 \
    && stderr ok "No cruft found ($tags)" \
    || stderr passed "Ignored $cruft cruft counts"
  rm $out
} || {
  warn "Crufty: $cruft counts ($tags)"
  ret=1
}

trueish "$exit" && exit $ret || exit 0

# Id: script-mpe/0.0.3 tools/sh/tags.sh
