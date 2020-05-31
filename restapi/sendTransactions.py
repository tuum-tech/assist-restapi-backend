import pymongo, requests, json, uuid
from datetime          import datetime, timedelta
from .mongoDatabase    import MongoDatabase
from .sidechainService import SidechainService


try:
    database = MongoDatabase()
    service = SidechainService()

    pendingTransactions = database.get_pending_transactions()

    transactions = []

    for pending in pendingTransactions:
        transactions.append(pending["didRequest"])

    if (transactions.count() > 0):
        blockTransaction = service.create_transaction(transactions)
        signedTransaction = service.sign_transaction(blockTransaction)
        sendResponse = service.send_transaction(signedTransaction) 

        
except Exception as e: 
    print(e)