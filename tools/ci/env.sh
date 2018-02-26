set -e

# Boilerplate env for CI scripts

. ./tools/sh/init.sh

test -n "$BASH_SH" || error "Need to know shell dist" 1
test 0 -eq $BASH_SH &&
    export SCR_SYS_SH=sh || export SCR_SYS_SH=bash-sh

. ./tools/sh/env.sh