#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: etc.py
@time: 2018/11/01
"""
from web3.utils.encoding import (hexstr_if_str, to_hex)

from source import config
from source.common.utils.log import get_logger
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.common.chain_driver.erc20_operator.utils.keyfile_op import load_keyfile
from source.model.database import Session, TbRecord
from source.common.address_manager import EtcManager


from . import BaseAPI


logger = get_logger(__name__)


class Etc(BaseAPI):
    def __init__(self):
        super().__init__("ETC")
    
    def get_address(self):
        manager = EtcManager(Session)
        address = manager.get_address()
        return {"pub_address": address.get("pub_address", ""),
                "tag": address.get("destination_tag", "")}

    def send2address(self, address, amount, *args, **kwargs):
        password = config.etc_password
        private_key = hexstr_if_str(
            to_hex, load_keyfile(config.etc_private_key_file, password))
        eth = ERC20Token(ipc_path=config.etc_ipc_path,
                         private_key=private_key,
                         password=password)
        checksum_address = eth.web3.toChecksumAddress(address)
        try:
            tx_id = eth.send_ether(checksum_address, amount)
            tb = {
                'amount': amount,
                'txid': tx_id,
                'coin_type': 'ETC',
                'from_address': config.etc_tb_address,
                'to_address': address,
            }
        except Exception as e:
            logger.exception(e)
        else:
            try:
                
                document = TbRecord(**tb)
                document.insert()
                return tx_id
            except Exception as e:
                logger.exception(e)
                logger.error("提币行为已经发生,但数据没有插入数据库{}".format(tb))
