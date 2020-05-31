# Assistt Rest API

To start, clone assist-restapi-backend repo
```
git clone https://github.com/tuum-tech/assist-restapi-backend.git;
cd assist-restapi-backend;
```

# Prerequisites
- Install required packages[Only needs to be done once]
```
./install.sh
```

# Run
- Start API server
```
./run.sh
```

# Verify
- To create a transaction, run the following:
```
curl http://localhost:8000/create?didid=didexemple&payload=test
```
- To verify the transaction, run the following:
```
curl http://localhost:8000/verify?transactionid=9f760fcd-9523-4899-9f58-44efdb2d3c7s
```