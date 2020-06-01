import pymongo

from app import config


class TransactionStatus(object):
    PENDING = "Pending"
    PROCESSING = "Processing"
    WAITING_CONFIRMATIONS = "Waiting confirmations"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


class Mongo:
    def __init__(self):
        host = config.MONGO['HOST']
        port = config.MONGO['PORT']
        username = config.MONGO['USERNAME']
        password = config.MONGO['PASSWORD']
        database_name = config.MONGO['DATABASE']
        client = pymongo.MongoClient("mongodb://{0}:{1}@{2}:{3}/".format(
                                            username, password, host, port))
        self.db = client[database_name]
        self.collection = "Transactions"
