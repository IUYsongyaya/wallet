
class BalanceNotSufficientError(Exception):
    def __init__(self, amount, balance):
        self.amount = amount
        self.balance = balance

    def __str__(self):
        return "ERROR: 余额不足，要提现{},　但钱包余额只有{}".format(self.amount,
                                                     self.balance)


class NotFoundCollection(Exception):
    def __init__(self, collection_name):
        self.msg_template = "not found {} collection in mongodb"
        super().__init__(self.msg_template.format(collection_name))


class RecordNotFound(Exception):
    def __str__(self):
        return "记录查询失败,无此记录"
