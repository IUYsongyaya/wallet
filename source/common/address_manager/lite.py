# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-11-15 下午4:01

from .btc import BtcManager
from source.model.database import Session
from source.common.chain_driver.bitcoin_operator.lite import LiteOp


class LiteAddressManager(BtcManager):

    def __init__(self, lite_rpc_uri, timeout, session_factory=Session):
        """
        :param session_factory: mysql_session_maker
        """
        super().__init__(session_factory)
        self.coin_category = "LITE"
        self.chain_api = LiteOp(lite_rpc_uri, timeout)
