#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: gather_poll.py
@time: 2018/09/09
"""
import datetime
import time

from source import config
from source.common.utils import log
from source.common.chain_driver.erc20_operator.erc20 import ERC20TokenChild
from source.model.database import Session, GatherStatusEnum
from source.model.encrypt_component import MCipher

from source.poll.erc_poll.base import BaseErcPoll


logger = log.get_logger(__name__, config.log_level)


class GatherPoll(BaseErcPoll):
    def __init__(self):
        super().__init__()
        self.erc_op_class = ERC20TokenChild
        self.encrypt_tool = MCipher()
    
    def get_account_info(self, address):
        """获取账户私钥密码
        :param address: 账户地址
        :return:
        """
        address_info = self.coin_address_coll.find_one({'pub_address': address})
        password = f'{config.passwd_prefix}_{address_info["account"]}'
        private_key = address_info['private_hash']
        parsed_private_key = self.encrypt_tool.decrypt(private_key)
        return password, parsed_private_key
    
    def token_withdraw_op(self, session, item):
        """token提现操作函数
        :param session: 数据库会话
        :param item: 交易信息
        """
        now = datetime.datetime.utcnow()
        password, private_key = self.get_account_info(item.from_address)
        token_info = session.query(
            self.coin_coll).filter_by(
            coin_type=item.coin_type, main_type="ETH").first()
        token_address = token_info.token_address
        token = self.erc_op_class(provider_endpoint=config.eth_wallet_url,
                                  contract_address=token_address,
                                  password=password,
                                  private_key=private_key,
                                  gas_price=10)
        
        try:
            amount = item.amount
            tx_id = token.send_tokens(
                item.to_address, amount, token_info.token_unit)
            logger.info(
                f"""{item.coin_type} child withdraw done:
                {item.to_address} {amount}""")
        except Exception as e:
            logger.exception("代币汇聚转账发生错误{}".format(e))
        else:
            item.tx_id = tx_id
            item.status = GatherStatusEnum.GATHERING
            item.updated_at = now
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                logger.exception("插入代币转账记录时数据库发生错误{}".format(e))
                
    def eth_withdraw_op(self, session, item):
        """eth 提现操作函数
        """
        now = datetime.datetime.utcnow()
        password, private_key = self.get_account_info(item.from_address)
        
        eth = self.erc_op_class(provider_endpoint=config.eth_wallet_url,
                                private_key=private_key,
                                password=password,
                                gas_price=10)
        try:
            amount = item.amount
            tx_id = eth.send_ether(item.to_address, amount)
            logger.info(f'ETH child withdraw done: {item.to_address} '
                        f'{amount}')
        except Exception as e:
            logger.exception("汇聚转账失败{}".format(e))
        else:
            item.tx_id = tx_id
            item.status = GatherStatusEnum.GATHERING
            item.updated_at = now
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                logger.exception("插入汇聚记录时数据库报错{}".format(e))
            
    def poll(self):
        logger.info("----------- eth_gather start -----------")
        session = Session()
        while True:
            try:
                coin_transfer_list = session.query(
                    self.coin_transfer_coll
                ).filter_by(status=GatherStatusEnum.GATHER,
                            coin_series="ETH").all()
                for item in coin_transfer_list:
                    if item.coin_type == 'ETH':
                        self.eth_withdraw_op(session, item)
                    else:
                        self.token_withdraw_op(session, item)
            except Exception as e:
                logger.exception("汇聚轮寻发生错误{}".format(e))
            time.sleep(10)


def main():
    poll_instance = GatherPoll()
    poll_instance.poll()
