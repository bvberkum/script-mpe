#!/usr/bin/env bash

# Initialize for ``sh-include PART..``

true "${U_S:="/srv/project-local/user-scripts"}"
true "${sh_tools:="$U_S/tools/sh"}"
true "${ci_tools:="$U_S/tools/ci"}"

. "$sh_tools/parts/fnmatch.sh"
. "$sh_tools/parts/include.sh"
. "$ci_tools/parts/print-err.sh"
