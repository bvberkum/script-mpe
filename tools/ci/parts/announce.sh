#!/bin/sh
# Announce build in CouchDB build-log record
set -e

curl -sSf https://$CI_DB_HOST/ || {
  echo "No remote DB, skipped build-log announce" >&2
  exit 0
}

node --version
# FIXME: nodejs deps needed, use curl instead

#  CI_DB_HOST="$CI_DB_HOST" \
#  CI_DB_INFO="$CI_DB_INFO" \
#  CI_DB_NAME='build-log' \
#      node ./tools/update-couchdb-testlog.js || {
#
#      echo "Ignored announcer failure" >&2
#      sleep 2
#      exit 0
#    }

# Id: script-mpe/0.0.4-dev tools/ci/parts/announce.sh
