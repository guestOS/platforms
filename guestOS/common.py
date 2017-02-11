# -*- coding: utf-8 -*-

from __future__ import print_function
from os import path

import os
import subprocess
import sys


color = lambda c: '\033[%sm' % c
color_string = lambda c, string: color(c) + string + color(0)

ok_green = lambda string: color_string(92, string)
ok_blue = lambda string: color_string(94, string)
warn = lambda string: color_string(93, string)
fail = lambda string: color_string(91, string)


class Bundle:
    def library_path(self, *path_components):
        lib_path = path.expanduser('~/Library/guestOS/')
        return path.join(lib_path, *path_components)

    def cache_path(self, *path_components):
        caches_path = path.expanduser('~/Library/Caches/guestOS/')
        return path.join(caches_path, *path_components)

    def bundle_path(self, *path_components):
        return path.join(path.dirname(path.dirname(__file__)), *path_components)

    def resource_path(self, *path_components):
        return self.bundle_path('Resources', *path_components)

    def downloads_path(self, *path_components):
        return path.join(self.ensure_dir(self.cache_path('Downloads')), *path_components)

    def intermediates_path(self, *path_components):
        return path.join(self.ensure_dir(self.cache_path('Intermediates')), *path_components)

    def products_path(self, *path_components):
        return path.join(self.ensure_dir(self.cache_path('Products')), *path_components)

    def ensure_dir(self, dir_path):
        if not path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path


bundle = Bundle()


class Command:
    def __init__(self, description, exit=True):
        self.description = description
        self.exit = exit

    def __enter__(self):
        print(self.description)

    def __exit__(self, type, value, traceback):
        if type is None:
            print(ok_green('Done'))
            return None

        if issubclass(type, EnvironmentError):
            print(fail(value.strerror) + (fail(': ') + value.filename) if value.filename else '')
        else:
            print(fail('Failed: ') + str(value))

        if self.exit:
            sys.exit(1)


def invoke_command(args, skip=False, passthrough=False, stdin=None, cwd=None, env=None, die=True):
    def log_command(message, command):
        joiner = '\n' + ' ' * len(message)
        exports = joiner.join(["export %s='%s'" % pair for pair in env.items()]) + joiner if env else ''
        change_dir = ('cd ' + cwd + joiner) if cwd else ''
        redirect = ' < ' + stdin.name if isinstance(stdin, file) else ''
        print(ok_blue(message) + exports + change_dir + command + redirect)

    command = ' '.join(args)
    if skip:
        log_command('Skipping: ', command)
        return

    log_command('Executing: ', command)
    env = merge(os.environ, env) if env else None
    stdout = subprocess.PIPE if not passthrough else None
    stderr = subprocess.PIPE if not passthrough else None
    proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
    _, stderr = proc.communicate()
    if proc.returncode != 0:
        color = fail if die else warn
        output = color(': ') + str(stderr.strip()) if stderr else ''
        print(color('Failed with exit code %s' % proc.returncode) + output)
        if die:
            sys.exit(1)
    else:
        print(ok_green('Done'))


def find(dir, name):
    output = subprocess.check_output(['find', dir, '-name', path.basename(name)])
    if ('/' in name):
        return '\n'.join([file for file in output.split('\n') if path.dirname(file) == path.dirname(name)])
    return output


def merge(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result
