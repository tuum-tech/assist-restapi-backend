import pymongo
import uuid
from datetime import datetime, timedelta

class TransactionStatus(object):
      PENDING = "Pending"
      PROCESSING = "Processing"
      WAITING_CONFIRMATIONS = "Waiting confirmations"
      SUCCEDED = "Succeded"
      FAILED = "Failed"



class MongoDatabase:
   
   def __init__(self):
      self.__client = pymongo.MongoClient("mongodb://mongoadmin:assistmongo@localhost:27017/")
      self.__db = self.__client["assistdb"]
      self.__TRANSACTIONS_COLLECTION = "Transactions"

   def create_transaction(self, didId, didRequest):
      collection = self.__db[self.__TRANSACTIONS_COLLECTION]
      transactionId = uuid.uuid4().hex
      transaction = {"_id": transactionId, "didid": didId, "didRequest": didRequest, "createdIn": str( datetime.utcnow() ), "status": TransactionStatus.PENDING, "lastUpdate": None, "blockchainTransaction": None  }
      collection.insert(transaction)
      return transaction
   
   def get_transaction(self, transactionId):
      collection = self.__db[self.__TRANSACTIONS_COLLECTION]
      query = {"_id": transactionId}
      response = collection.find(query)
      return response

   def get_transactions_from_didid(self, didId):
      collection = self.__db[self.__TRANSACTIONS_COLLECTION]
      query = {"didid": didId}
      response = collection.find(query)
      return response

   
   def get_pending_transactions(self):
      collection = self.__db[self.__TRANSACTIONS_COLLECTION]
      query = {"status": TransactionStatus.PENDING}
      response = collection.find(query)
      # updatedValues = { "$set": { "status": TransactionStatus.SENDING, "lastUpdate": str( datetime.utcnow() ) } }
      # collection.update_many(query, updatedValues)
      return response


   def update_transaction(self, transactionId, status):
      collection = self.__db[self.__TRANSACTIONS_COLLECTION]
      query = {"_id": transactionId}
      updatedValues = { "$set": { "status": status, "lastUpdate": str( datetime.utcnow() ) } }
      collection.update_one(query, updatedValues)



   
