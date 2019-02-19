# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-23 下午7:42

import logging

from . import BaseAPI
from source import config
from source.model.database import TbRecord, Session
from source.model.address_manager import BtcManager
from source.common.chain_driver.bitcoin_operator import USDTOP


logger = logging.getLogger('usdt-withdraw')


class USDTManager(BtcManager):
    def __init__(self, session_factory):
        """
        :param session_factory: mysql_session_maker
        """
        super().__init__(session_factory)
        self.coin_category = "USDT"


class USDT(BaseAPI):

    def __init__(self):
        super().__init__('USDT')

    def get_address(self):
        manager = USDTManager(Session)
        address = manager.get_address()
        return {"pub_address": address.get("pub_address", ""),
                "tag": address.get("destination_tag", "")}

    def send2address(self, address, amount, coin_type, **kwargs):
        return self.withdraw(address, amount)

    def withdraw(self, address, amount):
        usdt = USDTOP(config.usdt_rpc_uri, config.timeout)
        from_address = config.usdt_tb_address
        tx_id = ''
        data = {
            'from_address': config.usdt_tb_address,
            'coin_type': self.coin_type,
            'to_address': address,
            'amount': amount
        }
        try:
            tx_id = usdt.send_usdt(from_address, address, amount)
            data['txid'] = tx_id
        except Exception as e:
            logger.exception(e)
            logger.exception(f'提币出错{data}')
        try:
            logger.info('withdraw {} to {}'.format(self.coin_type, address))
            document = TbRecord(**data)
            document.insert()
            return tx_id
        except Exception as e:
            logger.error(f"提币写入数据库出错{data}")
            logger.exception(e)
