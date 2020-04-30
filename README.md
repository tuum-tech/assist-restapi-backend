# Assist dApp Rest API

To start, clone vouch-restapi-backend repo
```
git clone https://github.com/tuum-tech/assist-restapi-backend.git;
cd assist-restapi-backend;
```
# Prerequisites

1. Install Falcon API 
```
pip install falcon 
```
2. Install Gunicorn (Only on Mac or Linuc)
```
pip install gunicorn
```
3. Install Waitress (Only on Windows)
```
pip install waitress
```
4. Install PyMongo
```
pip install pymongo
```

4. Create Database instance
```
cd tools
.\mongo.sh
```

# Run the service

On Windows
```
waitress-serve --port=8000 restapi:api
```

On Mac or Linux
```
gunicorn restapi:api
```

To create a transaction, execute this exemple
```
curl "http://localhost:8000/create?didid=didexemple&payload=test"
```

To verify a transaction, execute this exemple
```
curl "http://localhost:8000/verify?transactionid=9f760fcd-9523-4899-9f58-44efdb2d3c7s"
```
