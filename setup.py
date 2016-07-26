#################################################################
# MET v2 Metadate Explorer Tool
#
# This Software is Open Source. See License: https://github.com/TERENA/met/blob/master/LICENSE.md
# Copyright (c) 2012, TERENA All rights reserved.
#
# This Software is based on MET v1 developed for TERENA by Yaco Sistemas, http://www.yaco.es/
# MET v2 was developed for TERENA by Tamim Ziai, DAASI International GmbH, http://www.daasi.de
# Current version of MET has been revised for performance improvements by Andrea Biancini,
# Consortium GARR, http://www.garr.it
#########################################################################################

from setuptools import setup, find_packages
import sys, os

version = '0.1'

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='met',
      version=version,
      description="Metadata Explorer Tool",
      long_description="""Terena - Metadata Explorer Tool""",
      classifiers=[
        '  Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Terena',
      author_email='',
      url='https://github.com/TERENA/met',
      license='BSD License',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=required,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
