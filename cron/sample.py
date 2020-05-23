import struct
import base58
import hashlib
import ecdsa
import tx_ela
import random
import binascii
import requests
import json
from electrumx.lib.hash import sha256, double_sha256, hash_to_hex_str, \
    hex_str_to_hash
from electrumx.lib.util import (pack_le_uint16, pack_le_int32, pack_le_uint32,
                                pack_le_int64, pack_le_uint64, pack_varint,
                                pack_varbytes)


# Address Type
STANDARD = 0xAC
REGISTERID = 0xAD
MULTISIG = 0xAE
CROSSCHAIN = 0xAF

# Parameters secp256r1
#  from http://www.secg.org/sec2-v2.pdf, par 2.4.2
secp256r1_p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
secp256r1_n = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
secp256r1_b = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
secp256r1_a = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC
secp256r1_Gx = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
secp256r1_Gy = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5

secp256r1_curve = ecdsa.ellipticcurve.CurveFp(secp256r1_p, secp256r1_a,
                                              secp256r1_b)
generator = ecdsa.ellipticcurve.Point(secp256r1_curve, secp256r1_Gx,
                                      secp256r1_Gy, secp256r1_n)

#
# These need to be changed if the wallet changes 
#
sender_address = "EKsSQae7goc5oGGxwvgbUxkMsiQhC9ZfJ3"
private_key= "1d5fdc0ad6b0b90e212042f850c0ab1e7d9fafcbd7a89e6da8ff64e8e5c490d2"
public_key = "03848390f4a687c247f4f662364c142a060ad10a03749178268decf9461b3c0fa5"                                      

def ecdsa_sign(private_key: str, data):
    if isinstance(data, str):
        data = bytes.fromhex(data)
    private_key = bytes.fromhex(private_key)
    data_hash = hashlib.sha256(data).digest()

    n = generator.order()

    randrange = random.SystemRandom().randrange
    secret = int.from_bytes(private_key, byteorder="big", signed=False)
    digest = int.from_bytes(data_hash, byteorder="big", signed=False)
    pub_key = ecdsa.ecdsa.Public_key(generator, generator * secret)
    pri_key = ecdsa.ecdsa.Private_key(pub_key, secret)

    signature = pri_key.sign(digest, randrange(1, n))
    r = signature.r.to_bytes(32, byteorder="big", signed=False)
    s = signature.s.to_bytes(32, byteorder="big", signed=False)

    return r + s

def get_code_from_pb(public_key: str):
    pub_bytes = bytes.fromhex(public_key)
    data_list = []
    data_list.append(struct.pack("B", len(pub_bytes)))
    data_list.append(pub_bytes)
    data_list.append(struct.pack("B", STANDARD))
    return b''.join(data_list).hex()

def address_to_programhash(address, as_hex):
    """
    Convert Base58 encoded address to public key hash

    :param address: Crypto currency address in base-58 format
    :type address: str, bytes
    :param as_hex: Output as hexstring
    :type as_hex: bool

    :return bytes, str: Public Key Hash
    """
    data = base58.b58decode(address.encode())
    programhash = data[:21]
    if as_hex:
        return programhash.decode("hex")
    else:
        return programhash

def send_raw_DID_transaction(signed_transaction):
    url = "http://localhost:30113"

    payload = {
            "method":"sendrawtransaction",
            "params": [signed_transaction]
    }
    response = requests.post(url, json=payload).json()
    print("response: %s" % response)

def get_raw_DID_transaction(signed_transaction):
    url = "http://localhost:30113"

    payload = {
            "method":"getrawtransaction",
            "params": {"txid":""+signed_transaction+"","verbose":True}
    }

    response = requests.post(url, json=payload).json()
    print("response: %s" % response)

def get_utxos():
    url = "http://localhost:30113"

    payload = '{"method":"listunspent","params":{"addresses": ["'+sender_address+'"] }}'
    #print("payload: %s" % payload)
    response = requests.post(url, json=json.loads(payload)).json()
    print("response: %s" % len(response["result"]))
    lowest_value = 0;
    for x in response["result"]:
        print ("in value is: %f" % float(x["amount"]))
        if ( float(x["amount"]) > .000001)  and (lowest_value == 0 or (float(x["amount"]) < lowest_value) ):
            print ("%f is less than %15.8f" % (float(x["amount"]), lowest_value))
            lowest_value = float(x["amount"])  
            selected_response = x
    #print ("selected response is: %s" % selected_response)
    #print ("selected value = %15.8f" % float(selected_response["amount"] ) )
    return selected_response["txid"], selected_response["assetid"], selected_response["amount"]


class did_payload:
    header = {}
    proof = {}
    payload = b''

class raw_tx:
    version = b'\x00' #default
    #tx_type = ("0a").decode("hex") # DID transaction
    tx_type = b'\x0a' # DID transaction
    payload_version = struct.pack("<B",0) # one byte
    attributes = {}
    inputs = {}
    output_count = struct.pack("<B",2) # one byte
    outputs1 = {}
    outputs2 = {}
    lock_time = struct.pack("<L",0) # 4 bytes
    program_count = struct.pack("<B",1) # one byte



def create_raw_transaction(payload_string ):
    fee = .000001
    json_payload = json.loads(payload_string)
    prev_txid = '' 
    did_string = json_payload["didid"] 
    spec= json_payload["didRequest"]["header"]["specification"]
    verification = json_payload["didRequest"]["proof"]["verificationMethod"]
    signature = json_payload["didRequest"]["proof"]["signature"]
    payload = json_payload["didRequest"]["payload"]

    utxo_txid, asset_id, value = get_utxos()

    didtx = did_payload()
    didtx.payload = str.encode(payload)
    #didtx.header["spec"] = b"elastos/did/1.0"
    didtx.header["spec"] = str.encode(spec)
    didtx.header["op"] = b"create"
    #didtx.header["txid"] = b"cd6dd63985ed458e8e4c5aa6ec4ef25d"
    didtx.header["prev_txid"] = str.encode(prev_txid)

    change = int((10**8) * (float(value) - fee))
    print("change = %s" % change)

    tx_header = tx_ela.DIDHeaderInfo(specification=didtx.header["spec"], operation=didtx.header["op"], previoustxid=didtx.header["prev_txid"])


    didtx.proof["type"] = b"ECDSAsecp256r1"
    #didtx.proof["verification"] = b"did:elastos:ii4ZCz8LYRHax3YB79SWJcMM2hjaHT35KN#primary"
    didtx.proof["verification"] = str.encode(verification)
    #didtx.proof["signature"] = b"2uot4Nxu-aaAg2rmL_8S9BIHZe7l63qquQSbqZkhumfNfP2n8RdX8fFnDS4eQvPbQNzXsdwZQb2vijHrrVBUug"
    didtx.proof["signature"] = str.encode(signature)

    tx_proof = tx_ela.DIDProofInfo(type=didtx.proof["type"], verification_method=didtx.proof["verification"], signature=didtx.proof["signature"])

    tx_payload = tx_ela.TxPayloadDIDOperation(header=tx_header, payload=didtx.payload, proof=tx_proof).serialize()

    #
    # Need to pull these from utxo's
    #
    #prev_txid = "0883e717fe2fd7184c92bd16dc276645d07897f91b192c7a4694fe77686dea3a"
    #asset_id = "a3d0eaa466df74983b5d7c543de6904f4c9418ead5ffd6d25814234a96db37b0"
    
    #sender_hashed_public_key = base58.b58decode_check(sender_address)[:21].encode("hex")
    sender_hashed_public_key = address_to_programhash(sender_address,False)
    #receiver_address = "EJrijXpAJmFmn6Xbjdh8TZgAYKS1KsK26N" 
    did_string = "did:elastos:ii4ZCz8LYRHax3YB79SWJcMM2hjaHT35KN#primary"
    did_hashed = address_to_programhash(did_string,False)
    print ("Did Hashed %s" % did_hashed)





    rtx = raw_tx()


    rtx.attributes["count"] = struct.pack("<B",1) # one byte
    rtx.attributes["usage"] = 129 #2 bytes
    rtx.attributes["data"] = b'1234567890'
    tx_attributes = tx_ela.TxAttribute(usage=rtx.attributes["usage"], data=rtx.attributes["data"]).serialize()

    rtx.inputs["count"] = struct.pack("<B",1) # 1 bytes 
    rtx.inputs["previous_index"] = 0 # 2 bytes
    rtx.inputs["sequence"] = 0

    tx_input = tx_ela.TxInputELA(prev_hash=hex_str_to_hash(utxo_txid), prev_idx=rtx.inputs["previous_index"], sequence=rtx.inputs["sequence"]).serialize()
    print("input: %s " % str(tx_input) )


    # DID requires 2 outputs.  The first one is DID string with amount 0 and the second one is change address and amount.  Fee is about 100 sela (.000001 ELA)
    output1 = tx_ela.TxOutputELA(
            asset_id=hex_str_to_hash(asset_id),
            value=0, output_lock=0, pk_script=did_hashed,output_type=None, output_payload=None ).serialize(tx_ela.TransferAsset)
    print("output: %s " % (output1) )

    output2 = tx_ela.TxOutputELA(
            asset_id=hex_str_to_hash(asset_id),
            value=change, output_lock=0, pk_script=sender_hashed_public_key,output_type=None, output_payload=None).serialize(tx_ela.TransferAsset)
    print("output: %s " % (output2 ))


    raw_tx_string = (
        rtx.tx_type
        + rtx.payload_version
        + tx_payload
        + rtx.attributes["count"]
        + tx_attributes
        + rtx.inputs["count"]
        + tx_input
        + rtx.output_count
        + output1
        + output2
        + rtx.lock_time
    )    

    code = get_code_from_pb(public_key)
    signature = ecdsa_sign(private_key, raw_tx_string)
    parameter = (struct.pack("B", len(signature)) + signature).hex()
    parameter_bytes = bytes.fromhex(parameter)
    code_bytes = bytes.fromhex(code)

    script = (
        pack_varint(len(parameter_bytes)) + parameter_bytes
        + pack_varint(len(code_bytes)) + code_bytes
    )

    real_tx = (
        rtx.tx_type
        + rtx.payload_version
        + tx_payload
        + rtx.attributes["count"]
        + tx_attributes
        + rtx.inputs["count"]
        + tx_input
        + rtx.output_count
        + output1
        + output2
        + rtx.lock_time
        + rtx.program_count
        + script
    )

    return real_tx

test_payload = """{
  "_id": "cd6dd63985ed458e8e4c5aa6ec4ef25d",
  "didid": "org.elastos.trinity.dapp.did",
  "didRequest": {
    "header": {
      "specification": "elastos/did/1.0",
      "operation": "create"
    },
    "payload": "eyJpZCI6ImRpZDplbGFzdG9zOmlpNFpDejhMWVJIYXgzWUI3OVNXSmNNTTJoamFIVDM1S04iLCJwdWJsaWNLZXkiOlt7ImlkIjoiI3ByaW1hcnkiLCJwdWJsaWNLZXlCYXNlNTgiOiJ0MUNpRHFWMlBFRFNGOEN2ZXRFaXBqUEpaUFBuVGJSN2Iyd2cxZTVBYW83bSJ9XSwiYXV0aGVudGljYXRpb24iOlsiI3ByaW1hcnkiXSwidmVyaWZpYWJsZUNyZWRlbnRpYWwiOlt7ImlkIjoiI3RlY2gudHV1bS5hY2FkZW15IiwidHlwZSI6WyJBcHBsaWNhdGlvblByb2ZpbGVDcmVkZW50aWFsIiwiR2FtZUFwcGxpY2F0aW9uUHJvZmlsZUNyZWRlbnRpYWwiLCJTZWxmUHJvY2xhaW1lZENyZWRlbnRpYWwiXSwiaXNzdWFuY2VEYXRlIjoiMjAyMC0wNC0yOVQwNDowNDo0MFoiLCJleHBpcmF0aW9uRGF0ZSI6IjIwMjUtMDQtMjhUMDQ6MDQ6NDBaIiwiY3JlZGVudGlhbFN1YmplY3QiOnsiYWN0aW9uIjoiTGVhcm4gRWxhc3RvcyBieSBwbGF5aW5nIGdhbWVzIGFnYWluc3QgZnJpZW5kcyIsImFwcHBhY2thZ2UiOiJ0ZWNoLnR1dW0uYWNhZGVteSIsImFwcHR5cGUiOiJlbGFzdG9zYnJvd3NlciIsImlkZW50aWZpZXIiOiJ0ZWNoLnR1dW0uYWNhZGVteSJ9LCJwcm9vZiI6eyJ2ZXJpZmljYXRpb25NZXRob2QiOiIjcHJpbWFyeSIsInNpZ25hdHVyZSI6Ikd0aHpvdE50cVNZUzRpdEpjZkM4VFRUUVJEajRCUFNKejliS3ZuM1BPRDBQcEMtX0wyTnJaRXhTVWpjaWlhcWJMazNaOFQtWGJvcmVJcF9vNU9TbXlnIn19XSwiZXhwaXJlcyI6IjIwMjUtMDMtMTlUMTU6MzY6NTNaIiwicHJvb2YiOnsiY3JlYXRlZCI6IjIwMjAtMDQtMjlUMDQ6MDQ6NDBaIiwic2lnbmF0dXJlVmFsdWUiOiJ1OXR5QmVySVhzLUZqQ0xOdDl1MGdRMTNoSElPUGh5VC10dTVjSHBNZjBJNE1rUEpXQ1IwSXJVQk5ORjQ5WDktOE5tYXpaOXEtSWo3NkZvSVFWcDZuQSJ9fQ",
    "proof": {
      "type": "ECDSAsecp256r1",
      "verificationMethod": "did:elastos:ii4ZCz8LYRHax3YB79SWJcMM2hjaHT35KN#primary",
      "signature": "2uot4Nxu-aaAg2rmL_8S9BIHZe7l63qquQSbqZkhumfNfP2n8RdX8fFnDS4eQvPbQNzXsdwZQb2vijHrrVBUug"
    }
  },
  "createdIn": "2020-05-07 16:21:59.503990",
  "status": "Pending",
  "lastUpdate": null
}"""

'''
json_payload = json.loads(test_payload)


txid = json_payload["_id"] 
did_string = json_payload["didid"] 
spec= json_payload["didRequest"]["header"]["specification"]
verification = json_payload["didRequest"]["proof"]["verificationMethod"]
signature = json_payload["didRequest"]["proof"]["signature"]
payload = json_payload["didRequest"]["payload"]

print("txid %s" % txid)
print("did_string %s" % did_string)
print("spec %s" % spec)
print("verification %s" % verification)
print("signature %s" % signature)
print("payload %s" % payload)
'''

#send real_tx in binary, Do not encode to hex
tx = create_raw_transaction(test_payload)

send_raw_DID_transaction(binascii.hexlify(tx).decode(encoding="utf-8"))

# get_raw_DID_transaction("b3a84bcea61ea6a349d89feee0a073a51a1fe02f9dd6813dd9a53a2e4f4c202c")