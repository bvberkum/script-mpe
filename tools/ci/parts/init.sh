#!/bin/dash

# Using dash to allow brace-expansion, just in the init script

note "Entry for CI pre-install / init phase"


git remote add bitbucket https://dotmpe@bitbucket.org/dotmpe-personal/script-mpe.git
git checkout bitbucket/$TRAVIS_BRANCH --hard


# Basicly if these don't run dont bother with anything,
# But cannot abort/skip a Travis build without failure, can they?

# This is also like the classic software ./configure.sh stage.


note "PWD: $(pwd && pwd -P)"
note "Whoami: $( whoami )"

note "CI Env:"
{ env | grep -i 'shippable\|travis\|ci' | sed 's/^/	/' >&2; } || noop

note "Build Env:"
build_params | sed 's/^/	/' >&2


test -z "$BUILD_ID" || {
  test ! -d build || {
    rm -rf build
    note "Cleaned build/"
  }
  mkdir -vp build
}

( mkdir -vp ~/.local && cd ~/.local/ && mkdir -vp  bin lib share )

not_trueish "$SHIPPABLE" || {
  mkdir -vp shippable/{testresults,codecoverage}
  test -d shippable/codecoverage
}

fnmatch "* basename-reg *" " $TEST_SPECS " && {
  test -e ~/.basename-reg.yaml ||
    cp basename-reg.yaml ~/.basename-reg.yaml
}


head -n 10 /usr/local/bin/bats

note "Done"
# Id: script-mpe/0.0.4-dev tools/ci/parts/init.sh
