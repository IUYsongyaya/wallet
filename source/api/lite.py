# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-11-15 下午3:15

from source import config
from .btc import Btc
from source.common.chain_driver.bitcoin_operator import LiteOp
from source.common.address_manager.lite import LiteAddressManager


class Lite(Btc):
    def __init__(self):
        super().__init__("BTC")
        self.manager_class = LiteAddressManager(config.lite_rpc_uri,
                                                config.timeout)
        self.driver = LiteOp(config.lite_rpc_uri, config.timeout)
