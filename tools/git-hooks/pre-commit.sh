#!/bin/ash

# Executes before commit-msg is determined, to check stage or tree and abort if desired

# See man 5 githooks


test -z "${scm_nok:-}" || exit $scm_nok

# TODO: limit output to about one screen max, about 80 lines;
# start with top-10's for below scans.


BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"


# Compare to-be committed against HEAD or emty for initial commit

if git rev-parse --verify HEAD >/dev/null 2>&1
then
	against=HEAD
else
	# Initial commit: diff against an empty tree object
	against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# Use config hooks.allownonascii to configure this check
# If you want to allow non-ASCII filenames set hooks.allownonascii to true.
allownonascii=$(git config --bool hooks.allownonascii) || true

# Redirect output to stderr.
exec 1>&2

# Cross platform projects tend to avoid non-ASCII filenames; prevent
# them from being added to the repository. We exploit the fact that the
# printable range starts at the space character and ends with tilde.
if [ "$allownonascii" != "true" ] &&
	# Note that the use of brackets around a tr range is ok here, (it's
	# even required, for portability to Solaris 10's /usr/bin/tr), since
	# the square bracket bytes happen to fall in the designated range.
	test $(git diff --cached --name-only --diff-filter=A -z $against |
	  LC_ALL=C tr -d '[ -~]\0' | wc -c) != 0
then
	cat <<\EOF
Error: Attempt to add a non-ASCII file name.

This can cause problems if you want to work with people on other platforms.

To be portable it is advisable to rename the file.

If you know what you are doing you can disable this check using:

  git config hooks.allownonascii true
EOF
	exit 1
fi

# If there are whitespace errors, print the offending file names and fail.
git diff-index --check --cached $against -- &&
  $LOG note "OK" "Git whitespace checked" ||
    $LOG warn "Not OK" "Git whitespace check failed"


test ! -x $HOME/.git-checks || {

  . ~/.git-checks
}


# From GIT Annex hooks

test ! -d .git/annex || {
  git annex pre-commit . || error "GIT Annex pre-commit hook failed" $?
}

# Id: script-mpe/0.0.4-dev tools/git-hooks/pre-commit.sh
