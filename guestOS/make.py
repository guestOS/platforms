# -*- coding: utf-8 -*-

from __future__ import print_function
from .common import Command, bundle, ok_blue, ok_green, invoke_command, find
from .generate import generate_platform
from .build import build_binutils
from .inject import inject_platforms
from os import path

import config
import os
import re
import shutil
import subprocess
import tempfile


def generate_sdk(platform, platform_dir, vms_dir, force=False):
    def invoke_vagrant(args, vms_dir, stdin=None):
        invoke_command(['vagrant'] + args,
                       env={'guestOS.vm.headless': ''},
                       cwd=vms_dir, stdin=stdin, passthrough=True)

    installed = bundle.library_path('VirtualMachines')
    if path.exists(path.join(installed, 'Vagrantfile')):
        print(ok_blue('Using installed Vagrant configuration: ') + installed)
        vms_dir = installed

    box = platform.box_name
    box_dir = path.join(vms_dir, box)
    sdk_src = path.join(box_dir, 'SDK')

    if not path.exists(sdk_src) or force:
        invoke_command(['cp', '-rf', bundle.resource_path('Scripts'), path.join(vms_dir, '')])
        invoke_vagrant(['up', box], vms_dir)
        invoke_vagrant(['provision', box], vms_dir)

        invoke_command(['rm', '-rf', sdk_src])
        invoke_command(['mkdir', '-p', box_dir])
        invoke_vagrant(['ssh', '-c', 'python /vagrant/Scripts/collect.py /vagrant/%s/SDK' % box, box], vms_dir)
        invoke_vagrant(['halt', box], vms_dir)
    else:
        print(ok_blue('Found cached SDK files at: ') + sdk_src)

    sdk_root = find(platform_dir, '*.sdk').strip()
    sdk_root_rel = path.relpath(sdk_root, path.dirname(platform_dir))
    with Command(ok_blue('Copying ') + path.join(sdk_src, '*') + ok_blue(' to ') + path.join(sdk_root_rel, '')):
        for dir_name in os.listdir(sdk_src):
            dir_path = path.join(sdk_src, dir_name)
            if path.isdir(dir_path):
                dest = path.join(sdk_root, dir_name)
                shutil.copytree(dir_path, dest)


def get_build_info():
    try:
        source_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path.dirname(__file__))
        source_revision = source_revision.strip()
    except:
        source_revision = None
    build_number = os.environ.get('TRAVIS_BUILD_NUMBER')
    return (build_number, source_revision)


def make(force_build=False, force_sdk_gen=False):
    build_number, source_revision = get_build_info()
    platforms = config.platforms
    build_binutils(platforms, force=force_build)
    derived_data = bundle.cache_path('DerivedData')
    directories = []
    for platform in platforms:
        platform_dir = generate_platform(platform, derived_data, build_number, source_revision)
        # copy binutils
        triplet = platform.target_triplet()
        tools_src = bundle.products_path(triplet, triplet)
        tools_dst = path.join(platform_dir, 'Developer', 'usr')
        tools_dst_rel = path.relpath(tools_dst, path.dirname(platform_dir))
        with Command(ok_blue('Copying ') + tools_src + ok_blue(' to ') + tools_dst_rel):
            shutil.copytree(tools_src, tools_dst)
        # copy Vagrantfile
        vms_dir = path.join(derived_data, 'guestOS', 'VirtualMachines')
        invoke_command(['mkdir', '-p', vms_dir])
        invoke_command(['cp', bundle.resource_path('Vagrantfile'), path.join(vms_dir, '')])
        # copy SDK files
        if platform.sdk:
            raise Exception('Unimplemented')
        else:
            generate_sdk(platform, platform_dir, vms_dir, force=force_sdk_gen)

        directories.append(platform_dir)
        print(ok_green('DerivedData: ') + path.join(derived_data, 'guestOS'))

    return directories


def copytree(src, dst, *args, **kwargs):
    if path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, *args, **kwargs)


def make_install(force_build=False, force_sdk_gen=False):
    platforms_dir = bundle.library_path('Platforms')
    invoke_command(['mkdir', '-p', platforms_dir])

    directories = make(force_build, force_sdk_gen)
    for platform_dir in directories:
        destination = path.join(platforms_dir, path.basename(platform_dir))
        invoke_command(['rm', '-rf', destination])
        invoke_command(['cp', '-r', platform_dir, destination])

    vagrant_file = 'Vagrantfile'
    with Command(ok_blue('Copying ' + vagrant_file)):
        vms_dir = bundle.library_path('VirtualMachines')
        bundle.ensure_dir(vms_dir)
        shutil.copy(bundle.resource_path(vagrant_file), path.join(vms_dir, vagrant_file))

    with Command(ok_blue('Copying scripts')):
        scripts_dir = bundle.library_path('Scripts')
        bundle.ensure_dir(scripts_dir)
        module, trampoline = ('guestOS', 'platform')
        ignore = shutil.ignore_patterns('*.pyc', '.DS_Store')
        copytree(bundle.bundle_path(module), path.join(scripts_dir, module), ignore=ignore)
        shutil.copy(bundle.bundle_path(trampoline), path.join(scripts_dir, trampoline))

    inject_platforms()


def make_test():
    output = subprocess.check_output(['xcodebuild', '-showsdks'], stderr=subprocess.PIPE)
    sdks = re.findall(r'-sdk (guestos\.[\w\.]+)', output)
    tests_dir = bundle.bundle_path('Tests')
    for sdk in sdks:
        print(ok_blue('Testing SDK: ') + sdk)
        for test_name in os.listdir(tests_dir):
            if not test_name.endswith('Test'):
                continue
            test_path = path.join(tests_dir, test_name)
            for configuration in ('Debug', 'Release'):
                print(ok_blue('Trying to build ') + test_name +
                      ok_blue(' in ') + configuration + ok_blue(' configuration'))
                build_dir = tempfile.mkdtemp(prefix='guestOS.Tests.')
                invoke_command(['xcodebuild', '-sdk', sdk, '-scheme', test_name, '-configuration', configuration,
                                '-derivedDataPath', build_dir], cwd=test_path, die=False)
        print(ok_green('Finished testing SDK: ') + sdk)


def register_command(subparsers):
    def main(args):
        if args.action != 'test':
            func = make_install if args.action else make
            func(args.force_build, args.force_sdk_gen)
        else:
            make_test()

    parser = subparsers.add_parser('make')
    parser.add_argument('action', choices=['install', 'test'], nargs='?',
                        metavar='install | test', help='Install Platforms After make | Test Intalled Platforms')
    parser.add_argument('--force-build', action='store_true', help='Force Download/Build')
    parser.add_argument('--force-sdk-gen', action='store_true', help='Force SDK Generation (if applicable)')
    parser.set_defaults(main=main)
