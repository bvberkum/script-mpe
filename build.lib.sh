#!/bin/sh

set -e


build_lib_load()
{
    true
}

# Set suites for bats, behat and python given specs
build_test_init() # Specs...
{
  test -z "$1" || SPECS="$@"
  test -n "$SPECS" || SPECS='*'

  # NOTE: simply expand filenames from spec first,
  # then sort out testfiles into suites based on runner
  local suite=/tmp/htd-build-test-suite-$(uuidgen).list
  project_tests $SPECS > $suite
  wc -l $suite
  test -s "$suite" || error "No specs for '$*'" 1
  BUSINESS_SUITE="$( grep '\.feature$' $suite | lines_to_words )"
  BATS_SUITE="$( grep '\.bats$' $suite | lines_to_words )"
  PY_SUITE="$( grep '\.py$' $suite | lines_to_words )"
  # SUITE="$(project_tests | lines_to_words)"
}

# TODO
build_matrix()
{
  echo
}


test_shell()
{
  test -n "$*" || set -- bats
  local verbosity=4
  echo "test-shell: '$@' '$BATS_SUITE' | tee $TEST_RESULTS.tap" >&2
  eval $@ $BATS_SUITE | tee $TEST_RESULTS.tap
}


# Run tests for DUT's
project_test() # [Units...|Comps..]
{
  test -n "$base" || error "project-test: base required" 1
  set -- $(project_tests "$@")
  local failed=/tmp/$base-project-test-$(uuidgen).failed

  while test $# -gt 0
  do
    test -z "$1" -o "$(basename "$1" | cut -c1)" = "_" && continue
    note "Testing '$1'..."
    case "$1" in
        *.feature ) $TEST_FEATURE -- "$1" || echo "$1" >>$failed ;;
        *.bats ) {
                bats "$1" || echo "$1" >>$failed
            } | $TAP_COLORIZE ;;
        *.py ) python "$1" || echo "$1" >>$failed ;;
        * ) warn "Unrecognized DUT '$1'" ;;
    esac
    shift
  done

  test -e "$failed" && {
    test ! -s "$failed" || {
      warn "Failed components:"
      cat $failed
    }
    rm "$failed"
    return 1
  }
  note "Project test completed succesfully"
}

# Echo test file names
project_tests() # [Units..|Comps..]
{
  test -n "$1" || set -- "*"
  while test $# -gt 0
  do
      any_unit "$1"
      any_feature "$1"
      case "$1" in *.py|*.bats|*.feature )
          test -e "$1" && echo "$1" ;;
      esac
    shift
  done | sort -u
}

project_files()
{
  test -z "$1" && git ls-files ||
  while test $# -gt 0
  do
    git ls-files "$1*sh"
    shift
  done | sort -u
}

any_unit()
{
  test -n "$1" || set -- "*"
  test -n "$package_build_unit_spec" ||
      package_build_unit_spec='test/py/$id.py test/$id-lib-spec.bats test/$id-spec.bats test/$id.bats'

  while test $# -gt 0
  do
    c="-_*" mkid "$1"
    mkvid "$1"
    for x in $(eval echo "$package_build_unit_spec")
    do
      test -x "$x" && echo $x
      continue
    done
    shift
  done
}

any_feature()
{
  test -n "$1" || set -- "*"
  while test $# -gt 0
  do
    c="-_*" mkid "$1"
    find test -iname "$id.feature" -o -iname "$id-lib-spec.feature" -o -iname "$id-spec.feature"
    #| cut -c3-
    shift
  done
}

test_any_feature()
{
  test -n "$TEST_FEATURE" || error "Test-Feature env required" 1
  info "Test any feature '$*'"
  test -n "$1" && {
    local features="$(any_feature "$@" | tr '\n' ' ')"
    test -n "$features" || error "getting features '$@'" 1
    note "Features: $features"
    echo $TEST_FEATURE $features || return $?;
    $TEST_FEATURE $features || return $?;

  } || {
    $TEST_FEATURE || return $?;
  }
}

test_watch()
{
  local watch_flags=" -w test/bootstrap/FeatureContext.php "\
" -w package.yaml -w build.lib.sh -w tools/sh/env.sh "
  local tests="$(project_tests "$@")" files="$(project_files "$@")"
  test -n "$tests" || error "getting tests '$@'" 1
  note "Watching files: $(echo $tests)"
  watch_flags="$watch_flags $(echo "$tests" | sed 's/^/-w /g' | tr '\n' ' ' )"\
" $(echo "$files" | sed 's/^/-w /g' | tr '\n' ' ' )"
  note "Watch flags '$watch_flags'"
  nodemon -x "htd run project-test $(echo $tests | tr '\n' ' ')" $watch_flags || return $?;
}

feature_watch()
{
  watch_flags=" -w test/bootstrap/FeatureContext.php "
  test -n "$1" && {
    local features="$(any_feature "$@")"
    note "Watching files: $features"
    watch_flags="$watch_flags $(echo $features | sed 's/^/-w \&/')"
    nodemon -x "$TEST_FEATURE $(echo $features | tr '\n' ' ')" $watch_flags || return $?;

  } || {
    $TEST_FEATURE || return $?;
    nodemon -x "$TEST_FEATURE" $watch_flags -w test || return $?;
  }
}

tested()
{
  local out=$1
  test -n "$out" || out=tested.list
  read_nix_style_file $out
}
totest()
{
  local in=$1 out=$2 ; shift 2
  test -n "$in" || in=totest.list
  test -n "$out" || out=tested.list
  comm -2 -3 $in $out
}
retest()
{
  local in= out= #$1 out=$2 ; shift 2
  test -n "$in" || in=totest.list
  test -n "$out" || out=tested.list
  test -e "$in" || touch totest.list
  test -e "$out" || touch tested.list
  test -s "$in" || {
    project_tests "$@" | sort -u > $in
  }
  while true
  do
    # TODO: do-test with lst watch
    read_nix_style_file "$in" | while read test
    do
        grep -qF "$test" "$out" && continue
        note "Running '$test'... ($(( $(count_lines "$in") - $(count_lines "$out") )) left)"
        ( htd run test "$test" ) && {
          echo $test >> "$out"
        } || {
          warn "Failure <$test>"
        }
    done
    note "Sleeping for a bit.."
    sleep 60 || return
    note "Updating $out"
    cat "$out" | sort -u > "$out.tmp"
    diff -q "$in" "$out.tmp" >/dev/null && {
      note "All tests completed" && rm "$in" "$out.tmp" && break
    } || {
      mv "$out.tmp" "$out"
      sleep 5 &&
        comm -2 -3 "$out" "$in" &&
        continue
    }
  done
}

# Checkout from given remote if it is ahead, for devops work on branch & CI.
# Allows to update from amended commit in separate (local/dev) repository,
# w/o adding new commit and (for some systems) getting a new build number.
checkout_if_newer()
{
  test -n "$1" -a -n "$2" -a -n "$3" || error checkout-if-newer.args 1
  test -z "$4" || error checkout-if-newer.args 2

  local behind= url="$(git config --get remote.$2.url)"
  test -n "$url" && {
    test "$url" = "$3" || git remote set-url $2 $3
  } || git remote add $2 $3
  git fetch $2
  behind=$( git rev-list $1..$2/$1 --count )
  test $behind -gt 0 && {
    from="$(git rev-parse HEAD)"
    git checkout --force $2/$1
    to="$(git rev-parse HEAD)"
    export BUILD_REMOTE=$2 BUILD_BRANCH_BEHIND=$behind \
        BUILD_COMMIT_RANGE=$from...$to
  }
}

checkout_for_rebuild()
{
  test -n "$1" -a -n "$2" -a -n "$3" || error checkout_for_rebuild-args 1
  test -z "$4" || error checkout_for_rebuild-args 2

  test -n "$BUILD_CAUSE" || export BUILD_CAUSE=$TRAVIS_EVENT_TYPE
  test -n "$BUILD_BRANCH" || export BUILD_BRANCH=$1

  export BUILD_COMMIT_RANGE=$TRAVIS_COMMIT_RANGE
  checkout_if_newer "$@" && export \
    BUILD_CAUSE=rebuild \
    BUILD_REBUILD_WITH="$(git describe --always)"
}

before_test()
{
  verbose=1 git-versioning check &&
  projectdir.sh run :bats:specs
}

tap2junit()
{
  perl $(which tap-to-junit-xml) --input $1 --output $2
}

list_builds()
{
  sd_be=couchdb_sh COUCH_DB=build-log \
      statusdir.sh be doc $package_vendor/$package_id > .tmp.json
  last_build_id=$( jq -r '.builds | keys[-1]' .tmp.json )

  sd_be=couchdb_sh COUCH_DB=build-log \
      statusdir.sh be doc $package_vendor/$package_id:$last_build_id > .tmp-2.json

  #jq -r '.tests[] | ( ( .number|tostring ) +" "+ .name +" # "+ .comment )' .tmp-2.json
  jq -r '.tests[] | "\(.number|tostring) \( if .ok then "pass" else "fail" end ) \(.name)"' .tmp-2.json

  {
    jq '.stats.total,.stats.failed,.stats.passed' .tmp-2.json |
        tr '\n' " "; echo ; } | { read total failed passed

      test 0 -eq $failed && {
          note "Last test $last_build_id passed (tested $passed of $total)"
      } || {
          error "Last test $last_build_id failed $failed tests (passed $passed of $total)"
      }
  }
}

list_sh_files()
{
  local exts="sh bash"
  git ls-files | while read path ; do

    test -s "$path" || continue

    fnmatch "*.*" "$(basename "$path")" && {

        for ext in $exts
        do case "$path" in *.$ext ) echo "$path" ; break ;; esac
        done
        continue
    }

    head -n 1 "$path" | grep -q '^\#\!.*sh' || continue
    echo "$path"
  done
}

list_sh_calls()
{
  while read scriptfile
  do
      coffee $scriptpath/sh.coffee $scriptfile ||
          error "in file $scriptfile"
  done | sort -u
}

build_docs()
{
  local shell_deps=.shell-deps
  test -e $shell_deps || {
      list_sh_files | list_sh_calls > $shell_deps
  }
  read_nix_style_file $shell_deps | grep '^[A-Za-z_][A-Za-z0-9_\.-]*$' | while read execname
  do
      # Skip non-executables, aliases, functions
      test -x "$(which "$execname")" || continue

      # Ignore common shell commands
      grep -qi "^$execname$" .shell-builtins && continue
      grep -qi "^$execname$" .shell-regulars && continue

      # Separate third-party from locally installed execs
      test -e "$scriptpath/$execname" && {

        # TODO make .build/docs/bin/$execname.html
        echo $execname

      } || {

        # TODO: check/compile into tools.yaml
        echo $execname
      }
  done

  # TODO: generate docs, either from tools.yaml, project.yaml
  # Generate:
  #   per command man pages
  #   appendix listing for internal or third-party shell regulars
}

build_remotes()
{
  true
}

scan_names()
{
  test -n "$1" || set -- .

  find "$1" -not -path '*.git*' \( \
    -name '*.JPG' \
 -o -name '*.jpeg' \
 -o -name '*.tiff' \
 -o -name '*.BMP' \
 -o -name '*.JPEG' \
 -o -name '*.GIT' \
 -o -name '*.PNG' \
 -o -name '*.PSD' \
 -o -name '*.TGA' \
 -o -name '*.TIFF' \)

  find "$1" -not -path '*.git*'  \( \
    -iname '._*' \
    -o -iname '.DS_Store' \
    -o -iname 'Thumbs.db' \
    -o -iname '~uTorrentPartFile*' \
  \)

  find "$1" -not -path '*.git*' -type d -empty
}

