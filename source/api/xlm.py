# -*- coding: utf-8 -*-
# @File :  xlm_poll.py
# @Author : lh
# @time : 18-11-12 下午8:47
from source import config
from source.common.utils.log import get_logger
from . import BaseAPI
from source.model.database import TbRecord, Session
from source.model.address_manager import XlmManager
from source.common.chain_driver.xlm import XlmOP

logger = get_logger('xlm_poll-withdraw')


class XLM(BaseAPI):
    def __init__(self):
        super().__init__("XLM")

    def get_address(self):
        # 生成地址
        manager = XlmManager(Session)
        address = manager.get_address()
        bind_address = {
            'pub_address': address['pub_address'],
            'destination_tag': address['destination_tag']
        }
        return bind_address

    def send2address(self, address, amount, destination_tag, **kwargs):
        # 提币接口
        from_address = config.xlm_tb_address
        xlm = XlmOP(config, config.xlm_tb_url)
        tb_data = {
            'from_address': from_address,
            'to_address': address,
            'coin_type': 'XLM',
            'destination_tag': destination_tag
        }
        try:
            transaction_info = xlm.create_transaction(from_address, address,
                                                      amount, destination_tag)
            tx_hash = transaction_info.get('hash', '')
            trans_title = transaction_info.get('title', '')
            trans_code = transaction_info.get('extras', '')
            # 交易成功
            if not (trans_title and trans_code):
                logger.info('trans done: {} {}, tx_id: {}'.format(address,
                                                                  amount,
                                                                  tx_hash))
                tb_data['txid'] = tx_hash
        except Exception as e:
            # 交易失败
            tb_data['error_msg'] = transaction_info['extras']['result_codes']['operations']
            logger.exception(e)
        try:
            # 交易成功与否，插入数据库
            document = TbRecord(**tb_data)
            document.insert()
            return tx_hash
        except Exception as e:
            # 交易发生,插入数据库失败
            logger.exception(e)
            logger.error("提币行为已经发生,但插入数据库失败,{}".format(tb_data))
