#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from argparse import ArgumentParser
from os import makedirs
from os.path import join, exists, dirname, basename
from platform import system
from shutil import copyfile
from subprocess import check_output
import os


def find(dir, name, negate=False):
    negation = ['-not'] if negate else []
    types = ['(', '-type', 'f', '-o', '-xtype', 'f', ')']
    command = ['find', dir] + negation + ['-name', basename(name)] + types
    output = check_output(command)
    if ('/' in name):
        return '\n'.join([file for file in output.split('\n') if dirname(file) == dirname(name)])
    return output


def destination(base, path):
    if system() == 'Linux':
        if '/gcc/x86_64-linux-gnu/' in path:  # workaround for crtbeginS.o stored in gcc directory
            path = '/usr/lib/x86_64-linux-gnu/' + basename(path)
    return join(base, path.lstrip('/'))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('destination', nargs=1, help='destination to gether files')
    args = parser.parse_args()

    libs = [
        "crt1.o",
        "crti.o",
        "crtn.o",
        "crtbegin*.o",
        "crtend*.o",
        "ld-*",
        "libc.*",
        "libc-*",
        "libc_*",
        "libdl-*",
        "libdl.*",
        "libm.so*",
        "libpthread*",
        "libmvec*",
        "libgcc.*",
        "libgcc_*",
        "libgccpp.*",
        "libstdc++*",

        "libdispatch.*",
        "libkqueue.*",
        "libpthread_workqueue.*",
        "libBlocksRuntime.*",
        "librt.*",

        "/usr/local/lib/libobjc*",

        "libfreetype.*",
        "libz.*",
        "libpng*",

        "libfontconfig.so.1*",
        "libexpat.*",

        "libcairo.so.2*",
        "libpixman*",
        "libxcb-shm.*",
        "libxcb-render.*",
        "libxcb.*",
        "libXrender.*",
        "libXext.*",
        "libXau.*",
        "libXdmcp.*",

        "libGL.so*",
        "libxcb-dri3.*",
        "libxcb-present.*",
        "libxcb-sync.*",
        "libxshmfence.*",
        "libglapi.*",
        "libXdamage.*",
        "libXfixes.*",
        "libX11-xcb.*",
        "libxcb-glx.*",
        "libxcb-dri2.*",
        "libXxf86vm.*",
        "libdrm.*",

        "libX11.so*",

        "libcrypto.so.1*",
        "libssl.so.1*",
        "libhunspell-*.so.*",
        "libhunspell.*"
    ]

    paths = []
    for lib in libs:
        output = find('/lib', lib) + find('/usr/lib', lib) + find('/usr/local/lib', lib)
        list = output.strip().split('\n')
        print('\033[92m' + lib + '\033[0m')
        print(list)
        paths.extend(list)
    paths = [path for path in paths if '/debug/' not in path]

    headers = ''
    headers += find('/usr/include', "*.h")
    headers += find('/usr/local/include', "*.h")
    headers += find('/usr/include/', '*.*', negate=True)  # c++ headers
    paths.extend(headers.strip().split('\n'))

    for path in paths:
        dest = destination(args.destination[0], path)
        print('Copying %s to %s' % (path, dest))
        if not exists(dirname(dest)):
            makedirs(dirname(dest))
        copyfile(path, dest)

    print('Done')
