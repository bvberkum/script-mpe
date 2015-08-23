#!/usr/bin/env bats

bin=match.sh

load helper

@test "no arguments no-op" {
  run ${bin}
  test $status -eq 1
  test "${lines[0]}" = "No command given, see \"help\" [match.sh:]"
}

@test "glob matches path" {
  run ${bin} glob 'test.*' test.name
  test $status -eq 0
  test -z "${lines[@]}"
  run ${bin} glob '*.name' test.name
  test $status -eq 0
  test -z "${lines[@]}"
  run ${bin} glob '*.*' test.name
  test $status -eq 0
  test -z "${lines[@]}"
  run ${bin} glob 'path/.*.ext' path/.name.ext
  test $status -eq 0
  test -z "${lines[@]}"
  run ${bin} glob './path/.*.ext' ./path/.name.ext
  test $status -eq 0
  test -z "${lines[@]}"
}

@test "lists var names" {
  run ${bin} var-names
  test $status -eq 0
  test "${lines[0]}" = "SZ SHA1_CKS MD5_CKS CK_CKS EXT NAMECHAR IDCHAR NAMEPART NAMEPARTS ALPHA PART OPTPART"
}

@test "lists var names in name pattern" {
  source ./match.sh
  match_load
  run match_name_pattern_opts ./@NAMEPARTS.@SHA1_CKS.@EXT
  test $status -eq 0
  test "${lines[0]}" = "SHA1_CKS"
  test "${lines[1]}" = "EXT"
  test "${lines[2]}" = "NAMEPARTS"
  test "$(echo ${lines[@]})" = "SHA1_CKS EXT NAMEPARTS"
}

@test "compile regex for name pattern" {
  source ./match.sh
  match_load
  match_name_pattern_test ./@NAMEPARTS.@SHA1_CKS.@EXT
  test $? -eq 0
  test "$grep_pattern" = "\.\/[A-Za-z_][A-Za-z0-9_,-]\{1,\}S\.[a-f0-9]\{40\}\.[a-z0-9]\{2,5\}"
}

@test "compile regex for name pattern (II)" {
  source ./match.sh
  match_load
  match_name_pattern ./@NAMEPARTS.@SHA1_CKS@OPTPART.@EXT
  test $? -eq 0
  test "$grep_pattern" = "\.\/[A-Za-z_][A-Za-z0-9_,-]\{1,\}S\.[a-f0-9]\{40\}\(\.\(partial\|part\|incomplete\)\)\?\.[a-z0-9]\{2,5\}"
}

@test "compile regex for name pattern (III)" {
  source ./match.sh
  match_load
  match_name_pattern ./@NAMEPARTS.@SHA1_CKS@PART.@EXT
  test $? -eq 0
  test "$grep_pattern" = "\.\/[A-Za-z_][A-Za-z0-9_,-]\{1,\}S\.[a-f0-9]\{40\}\.\(partial\|part\|incomplete\)\.[a-z0-9]\{2,5\}"
  match_name_pattern ./@NAMEPARTS.@SHA1_CKS@PART.@EXT PART
  test $? -eq 0
  test "$grep_pattern" = "\.\/[A-Za-z_][A-Za-z0-9_,-]\{1,\}S\.[a-f0-9]\{40\}\(.\(partial\|part\|incomplete\)\)\.[a-z0-9]\{2,5\}"
}

@test "compile regex for name pattern with" {
}
