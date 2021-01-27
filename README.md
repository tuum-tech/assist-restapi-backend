# Assist Rest API

To start, clone assist-restapi-backend repo
```
git clone https://github.com/tuum-tech/assist-restapi-backend.git;
cd assist-restapi-backend;
```

# Prerequisites
- Install docker at [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
- Install required packages[Only needs to be done once]
```
./install.sh
```

# Run
- Copy example environment file
```
cp .env.example .env
```
- Modify .env file with any number of wallets to use
- [OPTIONAL]: If you want to remove previous mongodb data and start fresh, remove the mongodb directory
```
rm -rf .mongodb-data
```
- Start API server
```
./run.sh start
```

# Verify
- To check whether the API is working:
``` 
curl http://localhost:8000
```
- To create a transaction, run the following:
```
curl -XPOST -H "Content-Type: application/json" -H "Accept: application/json" -d @test/example_did_request.json http://localhost:8000/v1/didtx/create
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
- To retrieve recent 5 requests for a particular DID:
```
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/didtx/recent/did/ii4ZCz8LYRhax3YB39SWJcMM2hjaHT35KD
```
- To retrieve recent 5 DID documents published for a particular DID:
```
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/documents/did/ii4ZCz8LYRhax3YB39SWJcMM2hjaHT35KD
```
- To retrieve recent 5 DID documents published for a particular DID from a cryptoname:
```
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/documents/crypto_name/kpwoods
```
- To retrieve service count for did_publish service for a particular DID:
```
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/service_count/did_publish/ii4ZCz8LYRhax3YB39SWJcMM2hjaHT35KD
```
- To retrieve service count for all the services for all the DIDs:
```
curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v1/service_count/statistics
```

# Deploy to production
- Set the value of "PRODUCTION" on .env to True
- Deploy
```
zappa deploy prod
```
- Schedule cron job
```
zappa schedule prod
```