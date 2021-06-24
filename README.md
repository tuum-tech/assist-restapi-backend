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
  rm -rf ~/.tuum-mongodb-data
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
  curl -XPOST -H "Content-Type: application/json" -H "Accept: application/json" -d @test/example_did_request2.json http://localhost:8000/v2/didtx/create
  ```
- To retrieve a particular transaction according to confirmation ID:
  ```
  curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v2/didtx/confirmation_id/5ed561723947b48ab7edc527
  ```
- To retrieve all transactions for a particular DID:
  ```
  curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v2/didtx/did/did:elastos:ii4ZCz8LYRHax3YB79SWJcMM2hjaHT35KN
  ```
- To retrieve recent 5 requests for a particular DID:
  ```
  curl -H "Authorization: assist-restapi-secret-key" http://localhost:8000/v2/didtx/recent/did/did:elastos:ii4ZCz8LYRHax3YB79SWJcMM2hjaHT35KN
  ```
- To check the tx details:
  ```
  curl -XPOST -H "Content-Type: application/json" \
  --data-raw '{
      "jsonrpc":"2.0",
      "method":"eth_getTransactionReceipt",
      "params":["0x8ada66c8dfaeee7a1ce996fd28b5b5caa59d8ab92ddde4e8b6498eed46da9fd7"],
      "id":1
  }' https://api.elastos.io/eid
  ```
- To check the balance of an address:
  ```
  curl -XPOST -H "Content-Type: application/json" \
  --data-raw '{
      "jsonrpc":"2.0",
      "method":"eth_getBalance",
      "params":["0x365b70f14e10b02bef7e463eca6aa3e75ca3cdb1", "latest"],
      "id":1
  }' https://api.elastos.io/eid
  ```
- To resolve DID:
  ```
  curl -XPOST -H "Content-Type: application/json" \
  --data-raw '{
      "jsonrpc":"2.0",
      "method":"did_resolveDID",
      "params": [{
          "did": "ieaqHhcz7wVmkVZLxAaPToGf2hb9CXAEh3",
          "all": false
      }],
      "id":1
  }' https://api.elastos.io/eid
  ```
