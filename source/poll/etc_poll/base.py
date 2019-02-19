#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: base.py
@time: 2018/10/31
"""
from abc import ABCMeta

from source.poll.erc_poll.base import BaseErcPoll, ErcTxPoll
from source.model.database import BlockInfo


class BaseEtcPoll(BaseErcPoll, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.block_info_coll = BlockInfo
        self.coin_category = "ETC"


class BaseEtcTxPoll(ErcTxPoll, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.block_info_coll = BlockInfo
        self.coin_category = "ETC"
