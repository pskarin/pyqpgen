#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='cotc-qpgen',
      version='1.0',
      description='Controllers implemented using qpgen',
      author='Per Skarin',
      author_email='per.skarin@control.lth.se',
      packages=['cotc', 'cotc.sim'],
      include_package_data=True
)
