#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: qtum.py
@time: 2018/10/23
"""
from .btc import BtcOP


class QtumOP(BtcOP):
    """qtum rpc operations
    """

    def __init__(self, rpc_uri, timeout):
        super().__init__(rpc_uri, timeout)
