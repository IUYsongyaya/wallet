#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: bch.py
@time: 2018/10/29
"""
from source import config
from source.common.chain_driver.bitcoin_operator import BchOP

from .btc import BtcManager


class BchManager(BtcManager):
    def __init__(self, session_maker):
        super().__init__(session_maker)
        self.coin_category = "BCH"
        self.chain_api = BchOP(config)
