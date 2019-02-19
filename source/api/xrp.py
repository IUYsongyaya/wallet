# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-24 下午5:09


import os
import logging

from source import config
from . import BaseAPI
from source.model.database import Session
from source.common.chain_driver.xrp import XrpOpt
from source.common.address_manager import XRPMongoManager


logger = logging.getLogger('xrp-eth')
private_key = os.getenv('ETH_PRIVATE_KEY')
password = os.getenv('ETH_PASSWORD')


class XRP(BaseAPI):
    def get_address(self):
        manager = XRPMongoManager(Session)
        address = manager.get_address() or dict()
        return address.get("pub_address", "")

    def send2address(self, **kwargs):
        uri = config.xrp_tb_url
        address = os.environ.get('xrp_tb_address')
        secret = os.environ.get('xrp_tb_secret')
        client = XrpOpt(uri, address, secret)
        destination = kwargs.get('address')
        amount = kwargs.get('amount')
        destination_tag = kwargs.get('destination_tag')
        source_tag = kwargs.get('source_tag', 0)
        try:
            assert isinstance(destination_tag, int)
            assert isinstance(source_tag, int)
            tx_id = client.send2address(destination,
                                        amount,
                                        destination_tag,
                                        source_tag)
            return tx_id
        except Exception as e:
            logger.exception(e)
            return ''
