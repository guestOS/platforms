# -*- coding: utf-8 -*-

from __future__ import print_function
from .common import invoke_command, ok_blue, ok_green, fail, warn
from os import path, chdir

import subprocess
import sys
import os


def check_symlinks(directory):
    for subpath in os.listdir(directory):
        fullpath = path.join(directory, subpath)
        if not path.islink(fullpath):
            continue
        # print(ok_blue('Checking symlink: ') + subpath)
        if not path.exists(path.join(directory, os.readlink(fullpath))):
            print(warn('Removing broken symlink: ') + fullpath)
            os.unlink(fullpath)


def get_plaforms():
    platforms_path = path.expanduser('~/Library/guestOS/Platforms/')
    return [path.join(platforms_path, subpath) for subpath in os.listdir(platforms_path) if '.platform' in subpath]


def inject_platforms():
    dt_paths = subprocess.check_output(['mdfind', 'kMDItemCFBundleIdentifier', '=', 'com.apple.dt.Xcode'])
    dt_paths = dt_paths.strip().split('\n')

    for dt_path in dt_paths:
        directory = path.join(dt_path, 'Contents', 'Developer', 'Platforms')
        check_symlinks(directory)
        for platform_path in get_plaforms():
            skip = path.islink(path.join(directory, path.basename(platform_path)))
            invoke_command(['ln', '-s', platform_path], skip, cwd=directory, die=False)


def register_command(subparsers):
    def main(args):
        inject_platforms()

    parser = subparsers.add_parser('inject')
    parser.set_defaults(main=main)
