#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: encrypt_component.py
@time: 2018/10/23
"""
from Crypto.Cipher import AES

from source import config


class MCipher(object):
    def __init__(self):
        self.key = config.salt
        self.aes = AES.new(self._pad(self.key), AES.MODE_ECB)

    def encrypt(self, raw):
        """加密"""
        data = self._pad(raw)
        encrypted_text = self.aes.encrypt(data)

        return encrypted_text

    def decrypt(self, enc):
        """解密"""
        raw = str(self.aes.decrypt(enc), encoding='utf-8', errors="ignore")

        return raw

    @staticmethod
    def _pad(text):
        while len(text) % 16 != 0:
            text += ' '
        return bytes(text, encoding='utf-8')
