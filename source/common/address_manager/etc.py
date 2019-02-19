#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: etc.py
@time: 2018/11/01
"""
from .erc_20 import ErcManager


class EtcManager(ErcManager):
    def __init__(self, session_maker):
        """
        :param session_maker: mysql_session_maker
        """
        super().__init__(session_maker)
        self.coin_category = "ETC"
