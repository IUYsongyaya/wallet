#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: main.py
@time: 2018/11/06
"""
import click
import sys

from source import config
from source.common.utils.log import get_logger
from source.model.database import Base, engine
from source.poll.wallets import WalletRechargeRemote, WalletWithdraw
from source.model.records import WithdrawRecord

from .address_assistant import create_address
from .poll_assistant import list_poll, run_poll, NotExited

logger = get_logger(__name__, config.log_level)


@click.group()
def cli():
    pass


@cli.group()
def poll():
    """有关轮训的操作命令"""
    pass


@cli.group()
def address():
    """有关币种地址命令"""
    pass


@cli.command()
def list_coin():
    """列出所支持的所有币种"""
    for coin in config.coin_category:
        click.echo(coin)
        

@cli.command()
def create_db():
    """创建数据库表"""
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        logger.exception("创建数据库表失败{}".format(e))
    else:
        click.echo("创建数据库表完成")


@cli.command()
def withdraw():
    recharge = WalletRechargeRemote(config)
    withdraw = WalletWithdraw(config)
    records = WithdrawRecord(config)
    from_address = withdraw.wallet_address()
    to_address = recharge.wallet_address()
    amount = 1
    txid = "78787788" #withdraw.transfer_to(recharge.wallet_address(), amount)
    records.insert(dict(
        txid=txid,
        amount=amount,
        from_address=from_address,
        to_address=to_address,
    ))


@poll.command()
@click.option('--coin_type', '-ct', required=True, type=str)
def list_all(coin_type):
    """列出该币种所有轮寻"""
    coin_type = coin_type.upper()
    if coin_type not in config.coin_category:
        click.echo("所选币种未开放在配置文件中")
        sys.exit(0)
    poll_list = list_poll(coin_type)
    click.echo(poll_list)


@poll.command()
@click.option('--coin_type', '-ct', required=True, type=str,
              help="请细化币种类型")
@click.argument('special_poll', type=str)
def run(coin_type, special_poll):
    """运行轮训"""
    coin_type = coin_type.upper()
    if coin_type not in config.coin_category:
        click.echo("所选币种未开放在配置文件中")
        sys.exit(0)
    try:
        click.echo(f"start run{coin_type}>>>>><<<<{special_poll}")
        run_poll(coin_type, special_poll)
    except NotExited:
        click.echo(f"该轮寻{special_poll}不存在")
    except Exception as e:
        logger.exception(e)


@address.command()
@click.option('--coin_type', '-ct', required=True, type=str,
              help="请细化币种类型")
@click.option('--count', '-c', default=1000000, type=int, show_default=True)
def create(count, coin_type):
    """批量创建币种地址"""
    coin_type = coin_type.upper()
    if coin_type not in config.coin_category:
        click.echo("所选币种未开放在配置文件中")
        sys.exit(0)
    try:
        create_address(coin_type, count)
    except Exception as e:
        logger.exception(e)
        click.echo("创建地址失败,日志已记录请联系工作人员")
    else:
        click.echo(f"批量创建{coin_type}币种的{count}地址已创建完毕")


if __name__ == "__main__":
    cli()
