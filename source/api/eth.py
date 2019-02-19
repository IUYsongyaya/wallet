# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-23 下午3:10

import logging
from decimal import Decimal

from web3.utils.encoding import (hexstr_if_str, to_hex)

from source import config
from . import BaseAPI
from source.model.database import TbRecord, CoinSetting, TbStatusEnum
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.common.chain_driver.erc20_operator.utils.keyfile_op import load_keyfile
from source.model.database import Session
from source.model.address_manager import ErcManager


logger = logging.getLogger('withdraw-eth')


class Eth(BaseAPI):
    def get_address(self):
        if self.coin_type == "ETH":
            manager = ErcManager(Session)
            address = manager.get_address()
            return {"pub_address": address.get("pub_address", ""),
                    "tag": address.get("destination_tag", "")}
        else:
            raise NotImplementedError

    def send2address(self, address, amount, coin_type, **kwargs):
        amount = Decimal(str(amount))
        if self.coin_type == 'ETH':
            return self.withdraw_eth(address, amount)
        else:
            return self.withdraw_token(address, amount, coin_type)

    @classmethod
    def withdraw_eth(cls, address, amount):
        private_key = hexstr_if_str(to_hex,
                                    load_keyfile(config.eth_private_key_file,
                                                 config.eth_password)
                                    )
        eth = ERC20Token(provider_endpoint=config.eth_wallet_url,
                         private_key=private_key,
                         password=config.eth_password)
        checksum_address = eth.web3.toChecksumAddress(address)
        try:
            tx_id = eth.send_ether(checksum_address, amount)
            tb = {
                'amount': amount,
                'txid': tx_id,
                'coin_type': 'ETH',
                'from_address': config.eth_tb_address,
                'to_address': address,
                'status': TbStatusEnum.TRANSFER
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

    @classmethod
    def withdraw_token(cls, to_address, amount, coin_type):
        token_info = CoinSetting.find_one({'id': coin_type,
                                           'main_coin': 'ETH'})
        if not token_info:
            logger.warning('不存在的币种类型{}'.format(coin_type))
            return
        token_address = token_info['token_address']
        private_key = hexstr_if_str(to_hex,
                                    load_keyfile(config.eth_private_key_file,
                                                 config.eth_password)
                                    )
        token = ERC20Token(
            provider_endpoint=config.eth_wallet_url,
            contract_address=token_address,
            password=config.eth_password,
            private_key=private_key)
        try:
            tx_id = token.send_tokens(to_address, amount,
                                      token_info['token_unit'])
            data = {
                'amount': amount,
                'txid': tx_id,
                'from_address': getattr(config, f'{coin_type}_tb_address'),
                'coin_type': coin_type,
                'to_address': to_address,
                'status': TbStatusEnum.TRANSFER
            }
            logger.info('withdraw {} to {}'.format(coin_type, to_address))
        except Exception as e:
            logger.exception(e)
        else:
            try:
                tb = TbRecord(**data)
                tb.insert()
                return tx_id
            except Exception as e:
                logger.exception(e)
                logger.error("提币行为已经发生,但数据没有插入数据库{}".format(data))
