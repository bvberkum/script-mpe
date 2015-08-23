#!/usr/bin/env bash

PREFIX=~/usr

test -n "$SRC_PREFIX" || SRC_PREFIX=$HOME

test -n "$PREFIX" || {
  echo "Not sure where to install"
  exit 1
}

test -d $SRC_PREFIX || mkdir -vp $SRC_PREFIX
test -d $PREFIX || mkdir -vp $PREFIX


install_bats()
{
  # Check for BATS shell test runner or install
  test -x "$(which bats)" || {
    echo "Installing bats"
    pushd $SRC_PREFIX
    git clone https://github.com/sstephenson/bats.git
    cd bats
    ./install.sh $PREFIX
    popd
    export PATH=$PATH:$PREFIX/bin
  }

  bats --version
}

install_mkdoc()
{
  echo "Installing mkdoc"
  pushd $SRC_PREFIX
  git clone https://github.com/dotmpe/mkdoc.git
  cd mkdoc
  git checkout devel
  PREFIX=~/usr/ ./configure && ./install.sh
  popd
  rm Makefile
  ln -s ~/usr/share/mkdoc/Mkdoc-full.mk Makefile
  make
}

# expecting cwd to be ~/build/dotmpe/script.mpe/ but asking anyway

install_pylib()
{
  # hack py lib here
  mkdir -vp ~/lib/py
  cwd=$(pwd)
  pushd ~/lib/py
  ln -s $cwd script_mpe
  popd
  tree -C -ifgup ~/lib
  export PYTHON_PATH=$PYTHON_PATH:~/lib/py
}

install_script()
{
  cwd=$(pwd)
  pushd ~/
  ln -s $cwd bin
  popd
  echo "pwd=$cwd"
  echo "bats=$(which bats)"
}

test "$1" = "run" && {

  install_bats
  install_mkdoc
  install_pylib
  install_script

} || {
  echo -n
}

# Id: script-mpe/0 install-dependencies.sh

