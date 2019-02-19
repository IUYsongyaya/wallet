# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-9-7 下午3:56

# 充币检测
import time
from source import config
import logging
from datetime import datetime

from eth_utils import to_normalized_address
from web3.utils.encoding import hexstr_if_str, to_hex

from source.common.utils.tools import from_unit
from source.model.database import Recharge, Session, BlockInfo, CoinSetting, Account
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.poll.rpc_call import recharge


coin_type = 'ETH'
logger = logging.getLogger('recharge')
block_info_document = BlockInfo
coin_address_document = Account
coin_recharge_document = Recharge
coin_setting_document = CoinSetting


def get_black_list():
    return [config.eth_tb_address]


def check_account_exists(session, address):
    rv = session.query(coin_address_document
                       ).filter_by(**{'pub_address': address})
    result = bool(rv.first())
    return result


def tx_process(session, tx_id, operator: ERC20Token):
    """交易处理函数"""

    tx_data = operator.get_transaction_data(tx_id)
    from_address = tx_data.from_address
    black_list = get_black_list()
    if from_address in black_list:
        return

    if not check_account_exists(session, tx_data.to_address):
        return

    coin = coin_type
    if tx_data.token_address:
        coin_info = session.query(
            coin_setting_document
        ).filter_by(coin_setting_document.token_address.in_(
            (tx_data.token_address, to_normalized_address(
                tx_data.token_address)))).first()
        if not coin_info:
            logger.error(f'not found token address: {tx_data.token_address}')
            return
        coin = coin_info.coin_type
        tx_data.token_amount = from_unit(
            tx_data.token_amount, coin_info.token_unit)

    recharge_record = session.query(coin_recharge_document
                                    ).filter_by(txid=tx_id).first()
    if recharge_record:
        return

    data = {
        'amount': tx_data.ether_amount,
        'txid': tx_id,
        'created_at': datetime.utcnow(),
        'confirmation_count': tx_data.num_confirmations,
        'from_address': tx_data.from_address,
        'to_address': tx_data.to_address,
        'coin_type': coin,
        'coin_series': coin_type,
    }
    r = Recharge(**data)
    session.add(r)
    try:
        session.commit()
    except Exception as e:
        logger.exception("冲币记录到数据库时发生错误{}".format(e))
        session.rollback()
        raise
    else:
        recharge(address=data["to_address"],
                 from_address=data["from_address"],
                 amount=float(data["amount"]),
                 txid=data["txid"],
                 coin_type=data["coin_type"],
                 confirmations=data["confirmation_count"],
                 status=0,
                 destination_tag=None)
        logger.info('检测到{}充币到{}{}个'.format(
            tx_data.from_address, tx_data.to_address,
            tx_data.ether_amount)
        )


def check_block(block_info, operator: ERC20Token):
    """检查区块是否回滚"""
    if not block_info:
        return False
    info = operator.get_block(int(block_info.block_num) + 1)
    if not info:
        return False
    if hexstr_if_str(to_hex, info['parentHash']) == block_info.block_hash:
        new_block_info = {'block_num': int(info['number']),
                          'block_hash': hexstr_if_str(to_hex, info['hash']),
                          'coin_type': coin_type}
    else:
        new_block_info = {
            'coin_type': coin_type,
            'block_num': int(block_info.block_num
                             ) - int(config.eth_confirmations),
        }
        roll_back_info = operator.get_block(new_block_info['block_num'])
        new_block_info['block_hash'] = hexstr_if_str(
            to_hex, roll_back_info['hash'])
        new_block_info = {'block_num': int(roll_back_info['number']),
                          'block_hash': hexstr_if_str(to_hex,
                                                      roll_back_info['hash']),
                          'coin_type': coin_type}
    return new_block_info


def init_block_info(session):
    """第一次初始化数据库区块信息"""
    block_info = session.query(BlockInfo).filter_by(
        coin_type=coin_type).first()
    if block_info:
        return

    while True:
        try:
            operator = ERC20Token(provider_endpoint=config.eth_wallet_url)
            info = operator.get_block(int(operator.get_block_number()))
            block_info = BlockInfo(**{'block_num': int(info['number']),
                                      'block_hash': hexstr_if_str(
                                          to_hex, info['hash']),
                                      'coin_type': coin_type})
            session.add(block_info)
            session.commit()
            logger.info('block_info init success')
            break
        except Exception as e:
            logger.exception("初始化区块失败{}".format(e))
            session.rollback()
        time.sleep(15)


def main():
    session = Session()
    init_block_info(session)
    while True:
        try:
            operator = ERC20Token(provider_endpoint=config.eth_wallet_url)
            # 获取区块信息及交易列表
            block_info = session.query(block_info_document
                                       ).filter_by(coin_type=coin_type).first()
            checked_block_info = check_block(block_info, operator)

            if not checked_block_info:
                continue

            tx_list = operator.get_block_tx_id_list(checked_block_info['block_num'])
            # 遍历交易列表
            for tx_id in tx_list:
                tx_process(session, hexstr_if_str(to_hex, tx_id), operator)
            logger.info(
                f'pull block finished: {checked_block_info["block_num"]}'
            )
        except Exception as e:
            logger.exception(e)
        else:
            block_info.block_hash = checked_block_info['block_hash']
            block_info.block_num = checked_block_info['block_num']
            try:
                session.commit()
            except Exception as e:
                logger.exception("更新区块发生错误{}".format(e))
                session.rollback()
        time.sleep(3)


if __name__ == '__main__':
    main()
