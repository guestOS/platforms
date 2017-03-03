#!/usr/bin/env bash

set -e
set -u
cd "`dirname \"$0\"`"

REVISION='d1eb9ad91e45af19d16c3ef9bb742eb9df822c5a'

rm -rf libobjc2
git clone http://github.com/gnustep/libobjc2
pushd libobjc2
git checkout $REVISION
popd

rm -rf build
mkdir build
cd build

cmake -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_ASM_FLAGS=-c -DTESTS=OFF ../libobjc2
make -j2
make install
