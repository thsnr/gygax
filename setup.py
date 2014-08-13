#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup

import gygax

setup(
        name="gygax",
        version=gygax.__version__,
        description="A minimalistic IRC bot",
        long_description=open("README").read(),
        author="Tiit Pikma",
        author_email="pikma@ut.ee",
        url="https://github.com/thsnr/gygax",
        packages=["gygax"],
        license="MIT",
        classifiers=[
            "Development Status :: 1 - Planning",
            "Environment :: No Input/Output (Daemon)",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.4",
            "Topic :: Communications :: Chat :: Internet Relay Chat",
            ],
    )
