#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: gunicorn_config.py
@time: 2018/11/20
"""
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
