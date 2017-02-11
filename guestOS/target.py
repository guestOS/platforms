# -*- coding: utf-8 -*-


class Platform:
    def __init__(self, name, arch, box_name=None, sdk=None):
        self.name = name
        self.arch = arch
        self.box_name = box_name
        self.sdk = sdk

    def __str__(self):
        return self.name + '.' + self.arch

    def target_triplet(self):
        return self.arch.lower() + '-' + self.name.lower()
