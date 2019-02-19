# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-24 下午5:16

import datetime
from source import config
from source.common.utils import log
from .base import MysqlAddressManager
from source.common.chain_driver.bitcoin_operator import BtcOP

logger = log.get_logger(__name__, config.log_level)


class XRPMongoManager(MysqlAddressManager):
    def __init__(self, session_maker):
        """
        :param session_maker: mysql_session_maker
        """
        super().__init__(session_maker)
        self.coin_category = "XRP"
        self.chain_api = BtcOP(config)

    def get_address(self)-> dict:
        """
        从db中获取一条未绑定的地址
        获取时判定该地址即将绑定
        :return:
        """
        address_collection = self._get_collection(config.coin_address)
        address = address_collection.find_one_and_update(
            {"coin_type": self.coin_category, "is_used": False},
            {"is_used": True}
        )
        if not address:
            logger.error("预留地址不足请尽快批量创建地址")
        return address

    def generate_address(self):
        """xrp所有地址只在后台批量生成，多client在线并发请求生成xrp地址可能出现重复tag."""
        pass

    def _get_last_destination_tag(self):
        address_collection = self._get_collection(config.coin_address)
        res = address_collection.find_one({'coin_type': self.coin_category},
                                          sort=[('destination_tag', -1)])
        last_destination_tag = int(res['destination_tag']) if res else 100000
        return last_destination_tag

    def bulk_create_address(self, cnt: int) -> dict:
        last_destination_tag = self._get_last_destination_tag()
        res = []
        for i in range(1, cnt + 1):
            now = datetime.datetime.now()
            account_name = '{}_{}_{}_{}'.format(self.coin_category,
                                                now.strftime('%Y%m%d'),
                                                cnt, now.timestamp())
            ret = self._address_template.copy()
            ret['account'] = account_name
            ret['destination_tag'] = str(last_destination_tag + i)
            ret['pub_address'] = config.xrp_cb_address
            ret['private_hash'] = config.xrp_cb_secret_key
            ret['coin_type'] = self.coin_category
            ret['created_at'] = now
            ret['updated_at'] = now
            res.append(ret)
        address_collection = self._get_collection(config.coin_address)
        address_collection.insert_many(res)
        logger.info(f'成功创建{cnt}个xrp地址')

