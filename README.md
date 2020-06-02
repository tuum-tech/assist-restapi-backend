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
- To check whether the API is working:
``` 
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000
```
- To create a transaction, run the following:
```
curl -XPOST -H "Authorization: assist-restapi-secret-key" -H "Content-Type: application/json" -H "Accept: application/json" -d @test/example_did_request.json http://localhost:8000/v1/didtx/create
```
will return something like:
``` 
{"meta": {"code": 200, "message": "OK"}, "data": {"confirmation_id": "5ed561723947b48ab7edc527"}}
```
- To retrieve all the transactions:
``` 
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/didtx
```
- To retrieve a particular transaction according to confirmation ID:
```
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/didtx/confirmation_id/5ed561723947b48ab7edc527
```
- To retrieve all transactions for a particular DID:
```
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/didtx/did/ii4ZCz8LYRhax3YB39SWJcMM2hjaHT35KD
```