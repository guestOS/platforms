# -*- coding: utf-8 -*-

from __future__ import print_function
from .common import Command, bundle, find, merge, ok_blue, ok_green, fail
from .target import Platform
from os import path
from xml.sax.saxutils import escape

import json
import os
import plistlib
import shutil
import sys


def substitute_variables(filename, variables):
    with open(filename) as f:
        text = f.read()
        for key, value in variables.items():
            value = escape(value)  # works under assumpltion that all plists are in XML format
            text = text.replace('${' + key + '}', value)
    with open(filename, 'w') as f:
        f.write(text)


def get_variables(platform, build_number=None, source_revision=None):
    build_number = str(build_number) if build_number else '1'
    source_revision = str(source_revision) if source_revision else 'local'
    (os_name, os_arch) = (platform.name, platform.arch)

    identifier = os_name.lower() + '.' + os_arch.lower()
    name = os_name + '.' + os_arch
    description = os_name + ' ' + os_arch
    variables = {'OSID': identifier, 'OSNAME': name, 'OSARCH': os_arch, 'OSDESC': description,
                 'GUESTOS_BUILD': build_number, 'GUESTOS_REVISION': source_revision}
    plist_path = bundle.resource_path('Settings', '%s.%s.plist' % (os_name, os_arch))
    with Command(ok_blue('Reading variables from: ') + plist_path):
        variables = merge(variables, plistlib.readPlist(plist_path))

    return variables


def generate_platform(platform, derived_data, build_number=None, source_revision=None):
    print(ok_blue('Generating platform: ') + str(platform))
    variables = get_variables(platform, build_number, source_revision)
    print(ok_blue('Variables: ') + json.dumps(variables, sort_keys=True, indent=4))

    template = 'guestOS.platform'
    componets = template.split('.')
    platform_name = '.'.join([componets[0], platform.name, platform.arch, componets[1]])
    platforms_path = path.join(derived_data, 'guestOS', 'Platforms')
    destination = path.join(platforms_path, platform_name)

    if path.exists(destination):
        with Command(ok_blue('Removing ') + destination):
            shutil.rmtree(destination)
    with Command(ok_blue('Copying %s to: ' % template) + destination):
        shutil.copytree(bundle.bundle_path(template), destination)

    patterns = ['*.plist', '*.xcplugindata', '*.xcspec']
    results = ''.join([find(destination, pattern) for pattern in patterns])
    plist_paths = results.strip().split('\n')
    for plist_path in plist_paths:
        with Command(ok_blue('Substituting variables in: ') + path.relpath(plist_path, platforms_path)):
            substitute_variables(plist_path, variables)

    icon_path = bundle.resource_path('Icons', '%s.icns' % platform.name)
    if path.exists(icon_path):
        with Command(ok_blue('Copying icon: ') + path.basename(icon_path)):
            shutil.copyfile(icon_path, path.join(destination, path.basename(icon_path)))
    else:
        print(ok_blue('Icon not found for ') + platform.name + ok_blue(' platform'))

    for lockfile in find(destination, '.gitlock').strip().split('\n'):
        os.unlink(lockfile)

    return destination


def register_command(subparsers):
    def main(args):
        platform = Platform(args.os, args.arch)
        generate_platform(platform, args.derived_data)

    parser = subparsers.add_parser('gen')
    parser.add_argument('--os', required=True, help='Operating System Name')
    parser.add_argument('--arch', required=True, help='Architecture Name')
    parser.add_argument('--derived_data', required=True, help='Derived Data Path')
    parser.set_defaults(main=main)
