# -*- coding: utf-8 -*-

from __future__ import print_function
from .common import Command, bundle, invoke_command, ok_blue
from .target import Platform
from os import path

import os
import shutil
import subprocess
import tempfile
import uuid


def download_file(url, force=False):
    dest = bundle.downloads_path(path.basename(url))
    if not path.exists(dest) or force:
        with Command(ok_blue('Downloading: ') + url):
            temp = path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            invoke_command(['curl', '-f', '-L', url, '-o', temp], passthrough=True)
            print(ok_blue('Caching downloaded file at: ') + dest)
            if path.exists(dest):
                os.unlink(dest)
            os.rename(temp, dest)
    else:
        print(ok_blue('Found cached: ') + url + ok_blue(' at ') + dest)
    return dest


def archive_info(filepath):
    gz, bz2, lzma = ('.tar.gz', 'tar.bz2', 'tar.lzma')
    if filepath.endswith(gz):
        return (gz, ['-xzf'])
    elif filepath.endswith(bz2):
        return (bz2, ['-xjf'])
    elif filepath.endswith():
        return (lzma, ['--lzma', '-xf'])
    else:
        raise Exception("Unsupported file format: %s" % path.basename(filepath))


def unarchive_file(filepath, dest_dir):
    extenstion, flags = archive_info(filepath)
    if not path.exists(dest_dir):
        os.makedirs(dest_dir)
    has_gnutar = subprocess.call(['which', 'gnutar']) == 0
    args = ['gnutar' if has_gnutar else 'tar'] + flags + [filepath]
    invoke_command(args, cwd=dest_dir)
    return path.join(dest_dir, path.basename(filepath[:len(filepath) - len(extenstion)]))


def configure_and_make_binutils(platform, source_dir, build_dir, install_dir):
    os_name, os_arch = (platform.name.lower(), platform.arch.lower())

    configure_options = []
    if os_arch in ('ia64', 'x86_64'):
        if os_name in ('linux', 'freebsd'):
            configure_options = ['--enable-64-bit-bfd']
        arch_flag = '-m64'
    else:
        arch_flag = '-m32'
    target = platform.target_triplet()

    cflags = [arch_flag, '-Wformat=0', '-Wno-error=deprecated-declarations', '-Wno-error=unused-value']
    args = [path.join(source_dir, 'configure'), '--prefix=' + install_dir, '--target=' + target] + configure_options
    invoke_command(args, env={'CFLAGS': ' '.join(cflags)}, cwd=build_dir, passthrough=True)
    invoke_command(['make'], cwd=build_dir, passthrough=True)
    invoke_command(['make', 'install'], cwd=build_dir, passthrough=True)


def cleanup_dir(directory):
    if path.exists(directory):
        shutil.rmtree(directory, ignore_errors=True)
    if not path.exists(directory):
        os.makedirs(directory)


def check_link(link_path, force=False):
    result = True
    if path.exists(link_path):
        if not path.exists(path.join(path.dirname(link_path), os.readlink(link_path))) or force:
            os.unlink(link_path)
        else:
            result = False
    return result


def build_binutils(platforms, force=False):
    version = '2.27'  # Note: with binutils 2.26 library constructors are not invoked on Linux
    url = 'https://ftp.gnu.org/gnu/binutils/binutils-%s.tar.gz' % version
    filepath = download_file(url, force)

    for platform in platforms:
        target = platform.target_triplet()
        products_dir = bundle.products_path()
        target_products = path.join(products_dir, target)
        if not check_link(target_products, force=force):
            print(ok_blue('Found cached products for target ') + target + ok_blue(' at ') + target_products)
            continue

        interm_dir = bundle.intermediates_path()
        source_dir = unarchive_file(filepath, path.join(interm_dir, 'Sources'))
        patch_file = bundle.resource_path('Patches', 'binutils-%s.patch' % version)
        with open(patch_file) as patch:
            invoke_command(['patch', '-p1'], stdin=patch, cwd=source_dir)

        build_dir = path.join(interm_dir, 'DerivedData', path.basename(source_dir))
        cleanup_dir(build_dir)

        install_dir = path.join(interm_dir, 'Products', target)
        cleanup_dir(install_dir)
        configure_and_make_binutils(platform, source_dir, build_dir, install_dir)

        invoke_command(['rm', '-rf', source_dir])
        invoke_command(['rm', '-rf', build_dir])
        invoke_command(['ln', '-s', path.relpath(install_dir, products_dir)], cwd=products_dir)


def register_command(subparsers):
    def main(args):
        build_binutils([Platform(args.os, args.arch)], force=args.force)

    parser = subparsers.add_parser('build')
    parser.add_argument('--os', required=True, help='Operating System Name')
    parser.add_argument('--arch', required=True, help='Architecture Name')
    parser.add_argument('--force', action='store_true', help='Force Download/Build')
    parser.set_defaults(main=main)
