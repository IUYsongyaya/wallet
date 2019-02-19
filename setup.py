#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: setup.py.py
@time: 2018/09/09
"""
from setuptools import setup, find_packages

with open("requirements.txt", 'r') as fd:
    install_requires = fd.read().splitlines()


setup(name="wallet",
      version="0.0.1",
      description="crush3.0 wallet",
      long_description="",
      author="",
      author_email="",
      url="",
      license='MIT',
      packages=find_packages(exclude=['docs']),
      include_package_data=True,
      zip_safe=True,
      install_requires=install_requires,
      entry_points={'console_scripts': [
          'wallet_cli = source.command.main:cli']})
