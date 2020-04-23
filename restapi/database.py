from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime
engine = create_engine('postgresql+psycopg2://ast:ast@localhost:5438/assistdb', echo = True)
meta = MetaData()

transactions = Table(
   'Transactions', meta, 
   Column('transactionId', String, primary_key = True), 
   Column('didid', String), 
   Column('signedPayload', String), 
   Column('status', String), 
   Column('createdIn', DateTime), 
   Column('lastUpdate', DateTime, nullable=True)
)

didCounter = Table(
   'DidCounter', meta, 
   Column('didid', String, primary_key = True), 
   Column('counter', Integer), 
)

meta.create_all(engine)

