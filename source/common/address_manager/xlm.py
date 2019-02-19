# -*- coding: utf-8 -*-
# @File :  xlm_poll.py
# @Author : lh
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import copy
import datetime
from source.common.utils import log, tools
from source import config
from .base import MysqlAddressManager
from source.model.database import Session, Account

logger = log.get_logger(__name__, config.log_level)


class AddressManager(MysqlAddressManager):
    def __init__(self, session_factory=Session):
        """
        :param session_factory: mysql_session_maker
        """
        super().__init__(session_factory)
        self.coin_type = config.coin_type.upper()

    def generate_address(self, cnt: int, latest_tag) -> dict:
        """
        xlm所有地址在后台批量生成,多client在线并发请求生成xlm地址可能会出现重复
        """
        logger.info('+' * 20)
        now = datetime.datetime.now()
        # last_destination_tag = self.get_last_destination_memo()
        account_name = '{}_{}_{}_{}'.format(self.coin_type,
                                            now.strftime('%Y%m%d'),
                                            latest_tag + cnt,
                                            now.timestamp())
        ret = copy.deepcopy(self._address_template)
        ret['account'] = account_name
        ret['destination_tag'] = str(latest_tag + cnt)
        ret['pub_address'] = config.xlm_cb_address
        ret['coin_type'] = self.coin_category
        ret['private_hash'] = b''
        return ret

    def get_address(self,) -> dict:
        """
        从db中获取一条未绑定的地址
        获取时判定该地址即将绑定
        """
        try:
            address = self.db_connect.find_one_and_update(
                {'coin_type': self.coin_category, 'is_used': False},
                {'is_used': True}, return_res='new'
            )
        except NoResultFound:
            last_destination_tag = self.get_last_destination_memo()
            address = self.generate_address(1, last_destination_tag)
            # 存数据
            Account(**address).insert()
            tools.notify('预留xlm地址不足')
        return address

    def get_last_destination_memo(self):
        """
        从数据库里面捞最大的一条，否则直接从100000开始
        """
        res = self.db_connect.query(Account).filter_by(
            coin_type=self.coin_category
        ).order_by(desc(Account.destination_tag)).limit(1).one_or_none()
        last_destination_tag = int(res.destination_tag) if res else 100000
        return last_destination_tag

    def bulk_create_address(self, start: int, stop: int) -> dict:
        # 数据库里面捞最后一个
        last_destination_tag = self.get_last_destination_memo()
        # res = []
        for i in range(start, stop + 1):
            ret = self.generate_address(i, last_destination_tag)
            # res.append(ret)
            self.store_address(**ret)
        # self.db_connect.bulk_save_objects.add(res)
        logger.info(f'成功创建{stop}个xlm地址')
