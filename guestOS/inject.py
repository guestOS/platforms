# -*- coding: utf-8 -*-

from __future__ import print_function
from .common import invoke_command, ok_blue, ok_green, fail, warn
from os import path, chdir

import os
import plistlib
import subprocess
import sys


def check_symlinks(directory):
    for subpath in os.listdir(directory):
        fullpath = path.join(directory, subpath)
        if not path.islink(fullpath):
            continue
        # print(ok_blue('Checking symlink: ') + subpath)
        if not path.exists(path.join(directory, os.readlink(fullpath))):
            print(warn('Removing broken symlink: ') + fullpath)
            os.unlink(fullpath)


def check_compatibility_uuids(platform, plugins, uuid):
    for plugin_path in plugins:
        plist_path = path.join(plugin_path, 'Contents', 'Info.plist')
        info = plistlib.readPlist(plist_path)
        compatibility_uuids = info['DVTPlugInCompatibilityUUIDs']
        if not uuid in compatibility_uuids:
            plugin = path.basename(plugin_path)
            print(warn('Injecting compatibility UUID ') + uuid + warn(' in %s:%s' % (platform, plugin)))
            compatibility_uuids.append(uuid)
            plistlib.writePlist(info, plist_path)


def get_plaforms():
    platforms_path = path.expanduser('~/Library/guestOS/Platforms/')
    return [path.join(platforms_path, subpath) for subpath in os.listdir(platforms_path) if '.platform' in subpath]


def get_compatibility_uuid(dt_path):
    plist = path.join(dt_path, 'Contents', 'Info.plist')
    return subprocess.check_output(['defaults', 'read', plist, 'DVTPlugInCompatibilityUUID']).strip()


def inject_platforms():
    dt_paths = subprocess.check_output(['mdfind', 'kMDItemCFBundleIdentifier', '=', 'com.apple.dt.Xcode'])
    dt_paths = dt_paths.strip().split('\n')

    platform_plugins = {}
    for platform_path in get_plaforms():
        output = subprocess.check_output(['find', platform_path, '-name', '*.ideplugin'])
        platform_plugins[platform_path] = output.strip().split('\n')

    for dt_path in dt_paths:
        directory = path.join(dt_path, 'Contents', 'Developer', 'Platforms')
        check_symlinks(directory)
        uuid = get_compatibility_uuid(dt_path)
        for platform_path in get_plaforms():
            skip = path.islink(path.join(directory, path.basename(platform_path)))
            invoke_command(['ln', '-s', platform_path], skip, cwd=directory, die=False)
            check_compatibility_uuids(path.basename(platform_path), platform_plugins[platform_path], uuid)


def register_command(subparsers):
    def main(args):
        inject_platforms()

    parser = subparsers.add_parser('inject')
    parser.set_defaults(main=main)
