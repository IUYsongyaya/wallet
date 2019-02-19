#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: bch.py.py
@time: 2018/10/29
"""
from source import config
from source.common.chain_driver.bitcoin_operator import BchOP
from source.common.address_manager import BchManager

from .btc import Btc


class Bch(Btc):
    def __init__(self):
        super().__init__()
        self.coin_type = "BCH"
        self.manager_class = BchManager
        self.driver = BchOP()
