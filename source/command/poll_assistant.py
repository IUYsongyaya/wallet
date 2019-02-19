#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: poll_assistant.py
@time: 2018/11/06
"""
import importlib
from pathlib import Path


def get_poll_dir(coin_type):
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent
    poll_dir = root_dir / "poll" / (coin_type.lower() + "_poll")
    return poll_dir


def list_poll(coin_type):
    poll_dir = get_poll_dir(coin_type)
    files = [file.name.rstrip('.py') for file in poll_dir.iterdir() if
             file.name.endswith('poll.py') or file.name.endswith('balance.py')]
    return files


class NotExited(Exception):
    pass


def run_poll(coin_type, poll_name):
    poll_list = list_poll(coin_type)
    if poll_name not in poll_list:
        raise NotExited
    model_name = "." + coin_type.lower() + "_poll" + '.' + poll_name
    poll_model = importlib.import_module(model_name, package="source.poll")
    poll_model.main()
