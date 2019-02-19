#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: erc_20.py
@time: 2018/09/05
"""
import datetime
import copy

from source import config
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.common.chain_driver.erc20_operator.utils import keyfile_op

from .base import MysqlAddressManager


class ErcManager(MysqlAddressManager):
    def __init__(self, session_maker):
        """
        :param session_maker: mysql的session_maker
        """
        super().__init__(session_maker)
        self.coin_category = "ETH"
        self.chain_api = ERC20Token()
        
    def generate_address(self, cnt: int)-> dict:
        """
        产生erc20地址账户
        :param cnt: 编号
        :return:
        """
        now = datetime.datetime.now()
        filename = '{}_{}_{}_{}'.format(self.coin_category,
                                        now.strftime('%Y%m%d'),
                                        cnt, now.timestamp())
        password = '{}_{}'.format(config.passwd_prefix, filename)
        fn = '{}/{}'.format(config.priv_fn_path, filename)
        pub, priv = keyfile_op.create_keyfile(password, fn)
        ret = copy.deepcopy(self._address_template)
        ret['account'] = filename
        ret['pub_address'] = pub
        ret['private_hash'] = priv
        ret['coin_type'] = self.coin_category
        ret['created_at'] = now
        ret['updated_at'] = now
        return ret
