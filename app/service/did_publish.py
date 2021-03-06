# -*- coding: utf-8 -*-

import sys
import struct
import base58
import hashlib
import ecdsa
from app.blockchain import tx_ela
import random
from electrumx.lib.hash import hex_str_to_hash
from electrumx.lib.util import pack_varint

from app import log, config

from app.service import DidSidechainRpc

LOG = log.get_logger()


class DidPublish(object):

    def __init__(self):
        self.wallets = config.WALLETS
        self.current_wallet_index = 0
        self.did_sidechain_fee = 0.000001

    def create_raw_transaction(self, did, json_payload):
        LOG.info("Creating raw transaction...")
        spec = json_payload["header"]["specification"]
        operation = json_payload["header"]["operation"]
        verification = json_payload["proof"]["verificationMethod"]
        signature = json_payload["proof"]["signature"]
        payload = json_payload["payload"]

        try:
            did_sidechain_rpc = DidSidechainRpc()
            addresses = [self.wallets[self.current_wallet_index]["address"]]
            utxo_txid, asset_id, value, prev_idx = did_sidechain_rpc.get_utxos(addresses)
            wallet_exhausted = 0
            while float(value) < 0.000001:
                if wallet_exhausted == config.NUM_WALLETS:
                    LOG.info("None of the wallets have enough UTXOs to send a transaction")
                    return None
                self.current_wallet_index += 1
                if self.current_wallet_index > config.NUM_WALLETS - 1:
                    self.current_wallet_index = 0
                utxo_txid, asset_id, value, prev_idx = did_sidechain_rpc.get_utxos(addresses)
                wallet_exhausted += 1

            change = int((10 ** 8) * (float(value) - self.did_sidechain_fee))
            previous_txid = ""
            if operation == "update":
                previous_txid = json_payload["header"]["previousTxid"]
            tx_header = tx_ela.DIDHeaderInfo(specification=str.encode(spec), operation=str.encode(operation),
                                             previoustxid=str.encode(previous_txid))

            tx_proof = tx_ela.DIDProofInfo(type=b"ECDSAsecp256r1", verification_method=str.encode(verification),
                                           signature=str.encode(signature))
            tx_payload = tx_ela.TxPayloadDIDOperation(header=tx_header, payload=str.encode(payload),
                                                      proof=tx_proof).serialize()
            sender_hashed_public_key = self.address_to_programhash(self.wallets[self.current_wallet_index]["address"],
                                                                   False)
            did_hashed = self.address_to_programhash(did, False)

            # Variables needed for raw_tx
            tx_type = b'\x0a'  # DID transaction
            payload_version = struct.pack("<B", 0)  # one byte
            output_count = struct.pack("<B", 2)  # one byte
            lock_time = struct.pack("<L", 0)  # 4 bytes
            program_count = struct.pack("<B", 1)  # one byte
            tx_attributes = tx_ela.TxAttribute(usage=129, data=b'1234567890').serialize()
            tx_input = tx_ela.TxInputELA(prev_hash=hex_str_to_hash(utxo_txid), prev_idx=prev_idx,
                                         sequence=0).serialize()
            # DID requires 2 outputs.  The first one is DID string with amount 0 and the second one is change address
            # and amount.  Fee is about 100 sela (.000001 ELA)
            output1 = tx_ela.TxOutputELA(
                asset_id=hex_str_to_hash(asset_id),
                value=0, output_lock=0, pk_script=did_hashed, output_type=None, output_payload=None).serialize(
                tx_ela.TransferAsset)
            output2 = tx_ela.TxOutputELA(
                asset_id=hex_str_to_hash(asset_id),
                value=change, output_lock=0, pk_script=sender_hashed_public_key, output_type=None,
                output_payload=None).serialize(tx_ela.TransferAsset)

            raw_tx_string = (
                        tx_type + payload_version + tx_payload + program_count + tx_attributes + program_count + tx_input + output_count + output1 + output2 + lock_time)

            code = self.get_code_from_pb()
            signature = self.ecdsa_sign(raw_tx_string)
            parameter = (struct.pack("B", len(signature)) + signature).hex()
            parameter_bytes = bytes.fromhex(parameter)
            code_bytes = bytes.fromhex(code)
            script = (pack_varint(len(parameter_bytes)) + parameter_bytes + pack_varint(len(code_bytes)) + code_bytes)

            real_tx = (
                        tx_type + payload_version + tx_payload + program_count + tx_attributes + program_count + tx_input + output_count + output1 + output2 + lock_time + program_count + script)

            return real_tx
        except Exception as err:
            message = "Error: " + str(err) + "\n"
            exc_type, exc_obj, exc_tb = sys.exc_info()
            message += "Unexpected error: " + str(exc_type) + "\n"
            message += ' File "' + exc_tb.tb_frame.f_code.co_filename + '", line ' + str(exc_tb.tb_lineno) + "\n"
            LOG.info(f"Error while creating a transaction: {message}")
            return None

    def ecdsa_sign(self, data):
        # Parameters secp256r1 from http://www.secg.org/sec2-v2.pdf, par 2.4.2
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

        if isinstance(data, str):
            data = bytes.fromhex(data)
        private_key = bytes.fromhex(self.wallets[self.current_wallet_index]["private_key"])
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

    def get_code_from_pb(self):
        # Address Type
        standard = 0xAC

        pub_bytes = bytes.fromhex(self.wallets[self.current_wallet_index]["public_key"])
        data_list = []
        data_list.append(struct.pack("B", len(pub_bytes)))
        data_list.append(pub_bytes)
        data_list.append(struct.pack("B", standard))
        return b''.join(data_list).hex()

    def address_to_programhash(self, address, as_hex):
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

