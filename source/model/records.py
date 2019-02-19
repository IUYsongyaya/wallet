# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-2-1

import logging
from source import config
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from source.model.database import Gather, Recharge, GatherStatusEnum, AccountBalance, TbRecord, InformEnum, BlockInfo, \
    CoinSetting, Session, TbStatusEnum
from source.exception import RecordNotFound
from eth_utils import to_normalized_address


BALANCE_CREATE_ERR = "[ %s ] <%s> insert failed! ]" % (config.coin_type.upper(), AccountBalance.__tablename__)
BALANCE_UPDATE_ERR = "[ %s ] <%s> update failed! ]" % (config.coin_type.upper(), AccountBalance.__tablename__)
BALANCE_SELECT_ERR = "[ %s ] <%s> select failed! ]" % (config.coin_type.upper(), AccountBalance.__tablename__)

RECHARGE_CREATE_ERR = "[ %s ] <%s> insert failed! ]" % (config.coin_type.upper(), Recharge.__tablename__)
RECHARGE_UPDATE_ERR = "[ %s ] <%s> update failed! ]" % (config.coin_type.upper(), Recharge.__tablename__)
RECHARGE_SELECT_ERR = "[ %s ] <%s> select failed! ]" % (config.coin_type.upper(), Recharge.__tablename__)

GATHER_CREATE_ERR = "[ %s ] <%s> insert failed! ]" % (config.coin_type.upper(), Gather.__tablename__)
GATHER_UPDATE_ERR = "[ %s ] <%s> update failed! ]" % (config.coin_type.upper(), Gather.__tablename__)
GATHER_SELECT_ERR = "[ %s ] <%s> select failed! ]" % (config.coin_type.upper(), Gather.__tablename__)

WITHDRAW_CREATE_ERR = "[ %s ] <%s> insert failed! ]" % (config.coin_type.upper(), TbRecord.__tablename__)
WITHDRAW_UPDATE_ERR = "[ %s ] <%s> update failed! ]" % (config.coin_type.upper(), TbRecord.__tablename__)
WITHDRAW_SELECT_ERR = "[ %s ] <%s> select failed! ]" % (config.coin_type.upper(), Gather.__tablename__)


class Record:
    def __init__(self, configure):
        self.configure = configure
        print("coin_type:", configure.coin_type)
        print("coin_category:", configure.coin_category)
        self.coin_type = configure.coin_type
        self.coin_category = configure.coin_category if configure.coin_category else self.coin_type


class GatherRecord(Record):
    Gather = Gather
    
    def __init__(self, configure):
        super().__init__(configure)
        self.table = Gather
    
    def _gather_col_fmt(self, val):
        return dict(updated_at=datetime.utcnow(),
                    coin_type=self.coin_type,
                    coin_series=self.coin_category,
                    txid=val['txid'],
                    amount=val['amount'],
                    fee=val['fee'],
                    fee_coin=val.get('fee_coin', self.coin_category),
                    from_address=val['from_address'],
                    to_address=val['address'],
                    source_tag=val['source_tag'],
                    destination_tag=val['destination_tag'],
                    confirmation_count=val['confirmations'],
                    status=val['status'],
                    done_at=val.get('done_at', None))
    
    def insert(self, value):
        value['created_at'] = datetime.now()
        value['updated_at'] = datetime.now()
        value['coin_type'] = self.coin_type.upper()
        value['coin_series'] = self.coin_category.upper()
        value['fee_coin'] = self.coin_category.upper()
        value['status'] = GatherStatusEnum.GATHERING
        try:
            record = self.Gather(**value)
            record.insert()
        except Exception as e:
            logging.error(
                f"%s: Gather txid:%s, amount:%s to address %s (Insert gather record failed!)" % (
                    GATHER_CREATE_ERR, value["txid"], value["amount"], value["to_address"],))
            logging.exception(e)


class GatheringRecord(Record):
    Gather = Gather
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def __iter__(self):
        records = self.Gather.find({
            'coin_type': self.coin_type.upper(),
            'status': GatherStatusEnum.GATHERING
        })
        if not records:
            raise StopIteration
        
        for record in records:
            _doc = record.to_dict()
            if _doc.get("txid", None):
                yield _doc
    
    def __setitem__(self, key, value):
        value['updated_at'] = datetime.now()
        value['fee_coin'] = self.coin_category.upper()
        try:
            self.Gather.replace_one({
                'id': value.get('id', ''),
            }, value)
        except Exception as e:
            logging.error(
                f"%s: Gather txid:%s, amount:%s to address %s (Update gather record failed!)" % (
                    GATHER_UPDATE_ERR, value["txid"], value["amount"], value["to_address"],))
            logging.exception(e)


class RechargeRecord(Record):
    Recharge = Recharge
    
    def __init__(self, configure):
        super().__init__(configure)

    def _recharge_col_fmt(self, val):
    
        return dict(updated_at=datetime.utcnow(),
                    txid=val['txid'],
                    coin_type=self.coin_type,
                    coin_series=self.coin_category,
                    amount=val['amount'],
                    from_address=val['from_address'],
                    to_address=val['address'],
                    source_tag=val['source_tag'],
                    destination_tag=val['destination_tag'],
                    comment=val.get('comment', ''),
                    confirmation_count=val['confirmations'],
                    status=val['status'],
                    informed=val['informed'],
                    register=val.get('register', False),
                    done_at=val.get('done_at', None))
    
    def __getitem__(self, txid):
        try:
            ret = self.Recharge.find_one(
                {
                    'txid': txid,
                    'coin_type': self.coin_type,
                })
        except Exception as e:
            logging.error(
                f"%s: Recharge txid:%s (Select recharge record failed!)" % (RECHARGE_SELECT_ERR, txid))
            logging.exception(e)
            record = {}
        else:
            record = ret.to_dict() if ret else {}
            
        return record
    
    def insert(self, value):
        now = datetime.utcnow()
        try:
            value['created_at'] = now
            doc_ = self._recharge_col_fmt(value)
            new = self.Recharge(**doc_)
            new.insert()
        except Exception as e:
            logging.error(
                f"%s: Recharge txid:%s, amount:%s, to address %s (Insert recharge record failed!)" % (
                    RECHARGE_CREATE_ERR, value["txid"], value["amount"], value["to_address"]))
            logging.exception(e)
    
    def __setitem__(self, key, value):
        try:
            doc_ = self._recharge_col_fmt(value)
            self.Recharge.replace_one({
                'id': value.get('id', '')
            }, doc_)
        except Exception as e:
            logging.error(
                f"%s: Recharge txid:%s, amount:%s, to address %s (Update recharge record failed!)" % (
                    RECHARGE_UPDATE_ERR, value["txid"], value["amount"], value["to_address"]))
            logging.exception(e)


class WithdrawBalanceRecord(Record):
    AccountBalance = AccountBalance
    session = Session()
    
    def __init__(self, configure):
        super().__init__(configure)
        self.tb_address = configure.tb_address
        
    @property
    def balance(self):
        record = self.AccountBalance.find_one({
            'coin_type': '{}_TX'.format(self.coin_type.upper())
        })
        
        if record:
            ret = record.to_dict()
            return ret.get("balance", 0)
        else:
            return 0
    
    @balance.setter
    def balance(self, val):
        _doc = dict()
        utc_now = datetime.utcnow()
        _doc['coin_type'] = '%s_TX' % self.coin_type.upper()
        _doc['updated_at'] = utc_now
        _doc['balance'] = val
        _doc['address'] = self.configure.tb_address
        account_balance = self.session.query(
            self.AccountBalance).filter_by(
            coin_type='%s_TX' % self.coin_type).with_for_update().first()
        if account_balance:
            account_balance.coin_type = _doc['coin_type']
            account_balance.update_at = _doc['updated_at']
            account_balance.balance = _doc['balance']
        else:
            account_balance_ = self.AccountBalance(**_doc)
            self.session.add(account_balance_)
        try:
            self.session.commit()
        except Exception as e:
            logging.error(
                f"%s: Update account balance: %s (Update Account balance  record failed!)" % (BALANCE_UPDATE_ERR, val))
            logging.exception("更新余额表时发生错误{}".format(e))

            self.session.rollback()


class WithdrawRecord(Record):
    TbRecord = TbRecord
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def _tbrecord_col_fmt(self, val):
        return dict(updated_at=val.get('updated_at', datetime.utcnow()),
                    txid=val['txid'],
                    coin_type=self.coin_type,
                    amount=val['amount'],
                    from_address=val['from_address'],
                    to_address=val['address'],
                    source_tag=val['source_tag'],
                    destination_tag=val['destination_tag'],
                    confirmation_count=val['confirmations'],
                    status=val['status'],
                    informed=val['informed'],
                    error_msg=val.get('error_msg', ""))
    
    def __iter__(self):
        records = self.TbRecord.find({
            'coin_type': self.coin_type,
            'informed': InformEnum.NO
        })
        if not records:
            raise StopIteration
        
        for record in records:
            _doc = record.to_dict()
            if _doc.get("txid", None):
                yield _doc
    
    def __setitem__(self, key, value):
        
        informed_failed = f"%s:  Withdraw txid:%s amount:%s address:%s (Inform failed)" \
                          % (WITHDRAW_UPDATE_ERR, value["txid"], value["amount"], value["to_address"])
        
        update_confirms_failed = f"%s: Withdraw txid:%s amount:%s address:%s  (Update confirms failed)" \
                                 % (WITHDRAW_UPDATE_ERR, value["txid"], value["amount"], value["to_address"])
        _doc = self._tbrecord_col_fmt(value)
        try:
            self.TbRecord.replace_one({
                'id': value.get('id', ''),
            }, _doc)
        except Exception as e:
            logging.error(informed_failed if value["informed"] else update_confirms_failed)
            logging.exception(e)

    def insert(self, value):
        value["created_at"] = datetime.now()
        value['confirmation_count'] = 0
        value["status"] = TbStatusEnum.TRANSFER
        value["informed"] = False
        doc_ = self._tbrecord_col_fmt(value)
        try:
            self.TbRecord(**doc_).insert()
        except Exception as e:
            logging.error(
                f"%s: TbRecord txid:%s, amount:%s to address %s (Insert tb record failed!)" % (
                    GATHER_CREATE_ERR, doc_["txid"], doc_["amount"], doc_["to_address"],))
            logging.exception(e)
        

class BlockInfoRecord(Record):
    BlockInfo = BlockInfo
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def retrieve_head_block(self):
        rv = self.BlockInfo.find_one(dict(coin_type=self.coin_type))
        if not rv:
            raise RecordNotFound
        return rv["block_num"], rv["block_hash"]
   
    def save_head_block(self, val):
        new_info = self.BlockInfo(**val)
        new_info.insert()


class CoinSettingRecord(Record):
    CoinSetting = CoinSetting
    
    def __init__(self, configure):
        super().__init__(configure)
        session = Session()
        self._token_address = None
        token_info = session.query(self.CoinSetting).filter_by(coin_type=self.coin_type, main_type=self.coin_category).first()
        self._token_address = token_info.token_address
        
        
    @property
    def token_address(self):
        return self._token_address
