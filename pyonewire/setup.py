#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "pyonewire",
    version = "0.5.1",
    description = "Python interface to 1-Wire devices",
    author = "mike wakerly",
    author_email = "opensource@hoho.com",
    url = "http://code.google.com/p/pyonewire/",
    packages = [
      'pyonewire',
      'pyonewire.core',
      'pyonewire.master',
    ],
    package_dir = {
      'pyonewire': '',
    },
)
