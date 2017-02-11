#!/usr/bin/env bash

set -e
set -u
cd "`dirname \"$0\"`"

rm -rf libobjc2
git clone http://github.com/gnustep/libobjc2

rm -rf build
mkdir build
cd build

cmake -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_ASM_FLAGS=-c -DTESTS=OFF ../libobjc2
make -j2
make install
