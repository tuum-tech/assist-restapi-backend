import sqlalchemy as db
import uuid
from datetime import datetime, timedelta
from sqlalchemy import and_
from .database import engine, transactions, didCounter


class DbRepository:
    def createTransaction(self, didId, signedPayload):
        conn = engine.connect()

        query = db.select([didCounter]).where(didCounter.c.didid==didId)
        result = conn.execute(query)
        row = result.fetchone()
        counter = 0
        if row == None:
            counter = 1
            validated = didCounter.insert(None).values(didid=didId, counter=counter)
            conn.execute(validated)
        else:
            counter = row[1]+1
            validated = didCounter.update(None).values(counter=counter).where(didCounter.c.didid==didId)
            conn.execute(validated)
        
        

        transactionId  = uuid.uuid4()
        newTransaction = transactions.insert(None).values(transactionId=transactionId, didid=didId, signedPayload=signedPayload, createdIn=datetime.now(), status="Pending")
        conn.execute(newTransaction)
        return "Transaction {} | did counter {}".format(transactionId,counter )

    def verifyTransaction(self, transactionId):
        conn = engine.connect()
        query = db.select([transactions]).where(transactions.c.transactionId== transactionId)
        result = conn.execute(query)
        row = result.fetchone()
        if row == None:
            return "Not found"

        return row[3]
