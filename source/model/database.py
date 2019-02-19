import enum
import json
import datetime
from copy import deepcopy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, String, DateTime, Boolean,
    Integer, Enum, Text, create_engine, Index, BINARY, FLOAT
)

from source import config
from source.common.utils.log import get_logger


Base = declarative_base()
engine = create_engine(config.database_uri)
Session = sessionmaker(bind=engine)
logger = get_logger('database')


def default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.isoformat()


class MyBase(Base):
    __abstract__ = True

    def __init__(self, **kwargs):
        """
        兼容mongodb的习惯写法.
        如：
            >>> data = {'account': '20180112', 'pub_address': '0xabc'}
            >>> a = Account(**data)
            >>> session.add(a)
            >>> session.commit()

        也可以按照sqlalchemy的方式：
        如：
            >>> a = Account()
            >>> a.account = '20180112'
            >>> a.pub_address = '0xabc'
            >>> b = Account(account='20180112', pub_address='0xabc')
            >>> session.bulk_save_objects.add([a, b])
            >>> session.commit()

        :param kwargs: 该表所需字段
        """

        if not kwargs:
            return
        for key, values in kwargs.items():
            if key not in self.columns:
                raise Exception(f'{key}不是表{self.__tablename__}的字段.')
            setattr(self, key, values)

    @property
    def columns(self):
        return [item.name for item in self.__table__.columns]

    def __getitem__(self, item):
        """兼容mongodb字典访问形式"""

        if item not in self.columns:
            raise Exception(f"{item}不是表{self.__tablename__}的字段.")
        return getattr(self, item)

    def __setitem__(self, key, value):
        """兼容mongodb字典访问形式"""

        if key not in self.columns:
            raise Exception(f"{key}不是表{self.__tablename__}的字段.")
        setattr(self, key, value)

    def __repr__(self):
        return json.dumps(self.to_dict(), default=default)

    def to_dict(self):
        res = deepcopy(self.__dict__)
        del res['_sa_instance_state']
        return res

    def insert(self):
        """插入一条记录
        如:
            >>> b = BlockInfo(id=1)
            >>> b.insert()
        """

        session = Session()
        session.add(self)
        try:
            session.commit()
        except Exception as e:
            logger.exception(e)
            logger.error(f'数据库写入错误{self}')
            session.rollback()
        finally:
            session.close()

    @classmethod
    def find_one(cls, query_params):
        """
        兼容mongodb find_one
        如：
            >>> print(BlockInfo.find_one({'id': 1, 'coin_type': 'btc'}))
            >>> {'id': 1, 'block_hash': '0xabc', 'coin_type': 'btc', 'block_num': 12}
            
        :param query_params: dict
        :return: cls实例或None
        """

        session = Session()
        rv = session.query(cls).filter_by(**query_params).one_or_none()
        session.close()
        return rv

    @classmethod
    def find(cls, query_params):
        session = Session()
        rv = session.query(cls).filter_by(**query_params).all()
        session.close()
        return rv

    @classmethod
    def replace_one(cls, query_params, data, for_update=False):
        """
        兼容mongodb replace_one
        如:
            >>> BlockInfo.replace_one({'id': 1}, {'block_num': 1})

        或者：
            >>> b = BlockInfo.find_one({'id': 1})
            >>> b.block_num = 1
            >>> BlockInfo.replace_one({'id': b.id}, b)
        
        :param query_params: 查询条件
        :param data: 字典或者cls实例
        :param for_update: 是否加排它锁
        :return: None
        """

        assert isinstance(data, cls) or isinstance(data, dict)
        if isinstance(data, cls):
            data = data.to_dict()
        session = Session()
        if for_update:
            rv = session.query(cls).filter_by(**query_params).with_for_update().one()
        else:
            rv = session.query(cls).filter_by(**query_params).one()
        for key, value in data.items():
            if key not in rv.columns:
                raise Exception(f'{key}不是表{rv.__tablename__}的字段.')
            setattr(rv, key, value)
        session.add(rv)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f'数据库写入错误{data}')
            logger.exception(e)
        finally:
            session.close()

    @classmethod
    def find_one_and_update(cls, query_params, data, return_res='old'):
        """
        >>> BlockInfo.find_one_and_update({'id': 1}, {'is_used': True})

        :param query_params: 查询条件 dict
        :param data: dict
        :param return_res:　old返回更新前的值，new返回更新后的值
        :return: cls实例
        """

        session = Session()
        rv = session.query(cls).filter_by(**query_params).one()
        session.close()
        old = deepcopy(rv)
        for key, value in data:
            if key not in rv.columns:
                raise Exception(f'{key}不是表{rv.__tablename__}的字段.')
            setattr(rv, key, value)
        cls.replace_one({'id': rv.id}, rv)
        if return_res == 'old':
            return old
        elif return_res == 'new':
            return rv

    @classmethod
    def find_one_and_delete(cls, query_params):
        session = Session()
        rv = session.query(cls).filter_by(**query_params).delete()
        session.close()
        return rv


class TbStatusEnum(enum.IntEnum):
    TRANSFER = 0  # 转账中
    FAILED = -1  # 转账失败
    SUCCESS = 1  # 转账成功


class ConfirmEnum(enum.IntEnum):
    YES = 1  # 已通知
    NO = 0  # 未通知


InformEnum = ConfirmEnum
RegisterEnum = ConfirmEnum


class RechargeStatusEnum(enum.IntEnum):
    RECHARGE = 0  # 充值中
    FAILED = -1  # 充值失败
    SUCCESS = 1  # 充值成功


class GatherStatusEnum(enum.IntEnum):
    FAILED = -1  # 汇聚失败
    GATHER_NO_FEE = 0  # 申请未有充足费用
    GATHER = 1  # 申请汇聚中
    GATHERING = 2  # 汇聚处理
    SUCCESS = 3  # 汇聚成功


class AskFeeStatusEnum(enum.IntEnum):
    ASK_FAILED = -3  # 缴费发送失败(调用接口失败)
    FAILED = -1  # 缴费失败(发送完成确认失败)
    ASKING = 0  # 申请缴费中
    WAIT_CONFIRM = 1  # 等待确认
    SUCCESS = 2  # 缴费成功


class MixIn(object):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class Account(MixIn, MyBase):
    """账户地址表"""
    __tablename__ = config.coin_address
    account = Column(String(50))
    pub_address = Column(String(200))
    private_hash = Column(BINARY(200))
    destination_tag = Column(String(50))
    coin_type = Column(String(10))
    is_used = Column(Boolean, default=False)


Index('idx_address_tag', Account.pub_address, Account.destination_tag,
      unique=True)


class TbRecord(MixIn, MyBase):
    """提币记录表"""
    __tablename__ = config.tb_record

    txid = Column(String(128))
    coin_type = Column(String(10))
    amount = Column(FLOAT(precision="16,9"), default=0)
    from_address = Column(String(128))
    to_address = Column(String(128))
    source_tag = Column(String(50))
    destination_tag = Column(String(50))
    confirmation_count = Column(Integer, default=0)
    status = Column(Enum(TbStatusEnum))
    informed = Column(Enum(InformEnum), default=InformEnum.NO)
    error_msg = Column(Text)


class Recharge(MixIn, MyBase):
    """冲值记录"""
    __tablename__ = config.recharge_record

    txid = Column(String(128))
    coin_type = Column(String(10))
    coin_series = Column(String(10))
    amount = Column(FLOAT(precision="16,9"), default=0)
    from_address = Column(String(128))
    to_address = Column(String(128))
    source_tag = Column(String(50))
    destination_tag = Column(String(50))
    comment = Column(Text)
    confirmation_count = Column(Integer)
    status = Column(Enum(RechargeStatusEnum),
                    default=RechargeStatusEnum.RECHARGE)
    informed = Column(Enum(InformEnum), default=InformEnum.NO)
    register = Column(Enum(RegisterEnum), default=RegisterEnum.NO)
    done_at = Column(DateTime)


class Gather(MixIn, MyBase):
    """资金汇聚表"""
    __tablename__ = config.coin_gather

    coin_type = Column(String(10))
    coin_series = Column(String(10))
    txid = Column(String(128))
    amount = Column(FLOAT(precision="16,9"), default=0)
    fee = Column(FLOAT(precision="16,9"))
    fee_coin = Column(String(10))
    from_address = Column(String(128))
    to_address = Column(String(128))
    source_tag = Column(String(50))
    destination_tag = Column(String(50))
    confirmation_count = Column(Integer)
    status = Column(Enum(GatherStatusEnum), default=GatherStatusEnum.GATHER)
    done_at = Column(DateTime)


class AskFee(MixIn, MyBase):
    """缴费记录表"""
    __tablename__ = config.coin_ask_fee

    txid = Column(String(128))
    amount = Column(FLOAT(precision="16,9"))
    coin_type = Column(String(10))
    coin_series = Column(String(10))
    from_address = Column(String(128))
    to_address = Column(String(128))
    source_tag = Column(String(50))
    destination_tag = Column(String(50))
    fee = Column(FLOAT(precision="16,9"))
    fee_coin = Column(String(10))
    confirmation_count = Column(Integer)
    status = Column(Enum(AskFeeStatusEnum), default=AskFeeStatusEnum.ASKING)
    done_at = Column(DateTime)


class AccountBalance(MixIn, MyBase):
    """账户余额表"""
    __tablename__ = config.coin_account_balance

    address = Column(String(128))
    coin_type = Column(String(10))
    balance = Column(FLOAT(precision="16,9"))


class BlockInfo(MyBase):
    """区块信息表"""
    __tablename__ = config.block_info

    id = Column(Integer, primary_key=True, autoincrement=True)
    block_num = Column(Integer)
    block_hash = Column(String(128))
    coin_type = Column(String(128))


class CoinSetting(MyBase):
    """币种动态配置表"""
    __tablename__ = config.coin_setting

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_type = Column(String(10))  # 币种
    main_coin = Column(String(10))  # 主币种类型
    token_address = Column(String(128))  # 合约地址
    token_unit = Column(Integer)
    chargeConfirmLimit = Column(Integer, default=0)
    withdrawalConfirmLimit = Column(Integer, default=0)
    platformWalletAddress = Column(String(128))
    tb_max = Column(Integer, default=0)
    cz_max = Column(Integer, default=0)


if __name__ == '__main__':
    Base.metadata.create_all(engine)
