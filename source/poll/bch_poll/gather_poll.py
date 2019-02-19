#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: gather_poll.py
@time: 2018/10/29
"""
from source import config
from source.common.chain_driver.bitcoin_operator.bch import BchOP
from source.poll.btc_poll.gather_poll import GatherPoll


class BchGather(GatherPoll):
    def __init__(self):
        super().__init__()
        self.coin_category = "BCH"
        self.driver = BchOP(config)


def main():
    poll_instance = BchGather()
    poll_instance.poll()
