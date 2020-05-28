#!/usr/bin/python3

# Copyright (c) 2016-2018, Neil Booth
# Copyright (c) 2019, the ElectrumX authors
# Copyright (c) 2020, Elastos Foundation
# All rights reserved.
#
# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''Deserializer for Elastos special transaction types'''

from collections import namedtuple
import struct
import electrumx
from electrumx.lib.hash import sha256, double_sha256, hash_to_hex_str, \
    hex_str_to_hash
from electrumx.lib.tx import Deserializer, DeserializerAuxPow, Tx, ZERO, MINUS_1
from electrumx.lib.util import (pack_le_uint16, pack_le_int32, pack_le_uint32,
                                pack_le_int64, pack_le_uint64, pack_varint,
                                pack_varbytes)

# ELA Transaction Type
CoinBase = 0x00
RegisterAsset = 0x01
TransferAsset = 0x02
Record = 0x03
# Deploy = 0x04
SideChainPow = 0x05
# RechargeToSideChain = 0x06
WithdrawFromSideChain = 0x07
TransferCrossChainAsset = 0x08
RegisterProducer = 0x09
CancelProducer = 0x0a
UpdateProducer = 0x0b
ReturnDepositCoin = 0x0c
ActivateProducer = 0x0d
IllegalProposalEvidence = 0x0e
IllegalVoteEvidence = 0x0f
IllegalBlockEvidence = 0x10
IllegalSidechainEvidence = 0x11
InactiveArbitrators = 0x12
UpdateVersion = 0x13
RegisterCR = 0x21
UnregisterCR = 0x22
UpdateCR = 0x23
ReturnCRDepositCoin = 0x24
CRCProposal = 0x25
CRCProposalReview = 0x26
CRCProposalTracking = 0x27
CRCAppropriation = 0x28
CRCProposalWithdraw = 0x29

# DID Transaction Type
RegisterDID = 0x0a

TxVersionDefault = 0x00

# VoteType
Delegate = 0x00
CRC = 0x01
VoteProducerAndCR = 0x01


def int_to_byte(num: int):
    return struct.pack("B", num)


class TxAsset(
    namedtuple("TxAsset", "name description precision assettype recordtype")):
    '''Class representing the Elastos asset'''

    def serialize(self):
        return b''.join((
            pack_varbytes(self.name),
            pack_varbytes(self.description),
            int_to_byte(self.precision),
            int_to_byte(self.assettype),
            int_to_byte(self.recordtype)
        ))


class TxPayloadCoinbase(namedtuple("TxPayloadCoinbase", "content")):
    '''Class representing the Elastos transaction payload for Coinbase'''

    def serialize(self, payload_version):
        if len(self.content) == 0:
            return pack_varbytes(self.content)
        else:
            return pack_varbytes(self.content)


class TxPayloadRegisterAsset(
    namedtuple("TxPayloadRegisterAsset", "asset amount controller")):
    '''Class representing the Elastos transaction payload for Register Asset'''

    def serialize(self, payload_version):
        return b''.join((
            self.asset.serialize(),
            pack_le_int64(self.amount),
            self.controller
        ))


class TxPayloadRecord(namedtuple("TxPayloadRecord", "type content")):
    '''Class representing the Elastos transaction payload for Record'''

    def serialize(self, payload_version):
        return b''.join((
            pack_varbytes(self.type),
            pack_varbytes(self.content())
        ))


class TxPayloadSidechainPow(namedtuple("TxPayloadSidechainPow",
                                       "blockhash genesishash height signature")):
    '''Class representing the Elastos transaction payload for Sidechain Pow'''

    def serialize(self, payload_version):
        return b''.join((
            self.blockhash,
            self.genesishash,
            pack_le_uint32(self.height),
            pack_varbytes(self.signature)
        ))


class TxPayloadWithdrawFromSidechain(
    namedtuple("TxPayloadWithdrawFromSidechain",
               "height address sidechaintxhashes")):
    '''Class representing the Elastos transaction payload for WithdrawFromSidechain'''

    def serialize(self, payload_version):
        return b''.join((
            pack_le_uint32(self.height),
            pack_varbytes(self.address),
            pack_varint(len(self.sidechaintxhashes)),
            b''.join((txhash for txhash in self.sidechaintxhashes))
        ))


class TxPayloadTransferCrosschainAsset(
    namedtuple("TxPayloadTransferCrosschainAsset",
               "addresses indexes amounts")):
    '''Class representing the Elastos transaction payload for TransferCrosschainAsset'''

    def serialize(self, payload_version):
        _count = len(self.addresses)
        assert _count == len(self.indexes) == len(self.amounts)

        return b''.join((
            pack_varint(_count),
            b''.join((
                b''.join((
                    pack_varbytes(self.addresses[i]),
                    pack_varint(self.indexes[i]),
                    pack_le_int64(self.amounts[i])
                )) for i in range(_count)
            ))
        ))


class TxPayloadProducerInfo(
    namedtuple("TxPayloadProducerInfo",
               "ownerpb nodepb nickname url location netaddress signature")):
    '''Class representing the Elastos transaction payload for producer's information'''

    def serialize(self, payload_version):
        return b''.join((
            pack_varbytes(self.ownerpb),
            pack_varbytes(self.nodepb),
            pack_varbytes(self.nickname),
            pack_varbytes(self.url),
            pack_le_uint64(self.location),
            pack_varbytes(self.netaddress),
            pack_varbytes(self.signature)
        ))


class TxPayloadProcessProducer(
    namedtuple("TxPayloadProcessProducer", "ownerpb signature")):
    '''Class representing the Elastos transaction payload for processing producer'''

    def serialize(self, payload_version):
        return b''.join((
            pack_varbytes(self.ownerpb),
            pack_varbytes(self.signature)
        ))


class TxPayloadActiveProducer(
    namedtuple("TxPayloadActiveProducer", "nodepb signature")):
    '''Class representing the Elastos transaction payload for Activing producer'''

    def serialize(self, payload_version):
        return b''.join((
            pack_varbytes(self.nodepb),
            pack_varbytes(self.signature)
        ))


class DPoSProposal(
    namedtuple("DPoSProposal", "sponsor blockhash viewoffset signature")):
    '''Class representing the Elastos DPoS Proposal'''

    def serialize(self):
        return b''.join((
            self.serialize_unsigned(),
            pack_varbytes(self.signature)
        ))

    def serialize_unsigned(self):
        return b''.join((
            pack_varbytes(self.sponsor),
            self.blockhash,
            pack_le_uint32(self.viewoffset)
        ))

    def hash(self):
        _content = self.serialize_unsigned()
        return double_sha256(_content)


class ProposalEvidence(
    namedtuple("ProposalEvidence", "proposal header height")):
    '''Class representing the Elastos Proposal Evidence'''

    def serialize(self):
        return b''.join((
            self.proposal.serialize(),
            pack_varbytes(self.header),
            pack_le_uint32(self.height)
        ))


class TxPayloadDPoSIllegalProposals(
    namedtuple("TxPayloadDPoSIllegalProposals", "evidence compareEvidence")):
    '''Class representing the Elastos transaction payload for DPoS Illegal Proposal'''

    def serialize(self, payload_version):
        return b''.join((
            self.evidence.serialize(),
            self.compareEvidence.serialize()
        ))

    def hash(self):
        _content = self.serialize()
        return double_sha256(_content)


class DPoSProposalVote(
    namedtuple("DPosProposalVote", "proposalhash signer accept signature")):
    '''Class representing the Elastos DPoS Proposal Vote'''

    def serialize(self):
        return b''.join((
            self.serialize_unsigned(),
            pack_varbytes(self.signature)
        ))

    def serialize_unsigned(self):
        return b''.join((
            self.proposalhash,
            pack_varbytes(self.signer),
            int_to_byte(1) if self.accept else int_to_byte(0)
        ))

    def hash(self):
        _content = self.serialize_unsigned()
        return double_sha256(_content)


class VoteEvidence(namedtuple("VoteEvidence", "vote evidence")):
    '''Class representing the Elastos Vote Evidence'''

    def serialize(self):
        return b''.join((
            self.vote.serialize(),  # DPoSProposalVote
            self.evidence.serialize()  # ProposalEvidence
        ))


class TxPayloadDPoSIllegalVotes(
    namedtuple("DPoSIllegalVotes", "evidence compareEvidence")):
    '''Class representing the Elastos DPoS Illegal Votes'''

    def serialize(self, payload_version):
        return b''.join((
            self.evidence.serialize(),
            self.compareEvidence.serialize()
        ))

    def hash(self, payload_version):
        _content = self.serialize(payload_version)
        return double_sha256(_content)


class TxPayloadBlockEvidence(
    namedtuple("BlockEvidence", "header blockconfirm signers")):
    '''Class representing the Elastos Block Evidence'''

    def serialize(self, payload_version):
        return b''.join((
            self.serialize_unsigned(),
            self.serialize_others()
        ))

    def serialize_unsigned(self):
        return pack_varbytes(self.header)

    def serialize_others(self):
        _count = len(self.signers)
        return b''.join((
            pack_varbytes(self.blockconfirm),
            pack_varint(_count),
            b''.join((pack_varbytes(self.signers[i] for i in range(_count))))
        ))

    def hash(self, payload_version):
        _content = self.serialize(payload_version)
        return double_sha256(_content)


class DPoSIllegalBlocks(namedtuple("DPoSIllegalBlocks",
                                   "coinType blockHeight evidence compareEvidence")):
    '''Class representing the Elastos DPoS Illegal Blocks'''

    def serialize(self):
        return b''.join((
            self.serialize_unsigned(),
            self.evidence.serialize_others(),
            self.compareEvidence.serialize_others()
        ))

    def serialize_unsigned(self):
        return b''.join((
            pack_le_uint32(self.coinType),
            pack_le_uint32(self.blockHeight),
            self.evidence.serialize_unsigned(),
            self.compareEvidence.serialize_unsigned()
        ))

    def hash(self):
        _content = self.serialize_unsigned()
        return double_sha256(_content)


class SidechainIllegalEvidence(
    namedtuple("SidechainIllegalEvidence", "dataHash")):
    '''Class representing the Elastos illegal evidence for sidechain'''

    def serialize(self):
        return self.dataHash


class TxPayloadSidechainIllegalData(namedtuple("SidechainIllegalData",
                                               "illegalType height illegalSigner evidence compareEvidence genesisBlockAddress signs")):
    '''Class repressenting the Elastos illegal data for sidechain'''

    def serialize(self, payload_version):
        _count = len(self.signs)
        return b''.join((
            self.illegalType,
            pack_le_uint32(self.height),
            pack_varbytes(self.illegalSigner),
            self.evidence.serialize(),
            self.compareEvidence.serialize(),
            pack_varbytes(self.genesisBlockAddress),
            pack_varint(_count),
            b''.join((pack_varbytes(self.signs[i] for i in range(_count))))
        ))


class TxPayloadInactiveArbitrators(
    namedtuple("InactiveArbitrators", "sponsor blockHeight arbitrators")):
    '''Class representing the Elastos Transaction payload for Inactive Arbitrators'''

    def serialize(self, payload_version):
        _count = len(self.arbitrators)
        return b''.join((
            pack_varbytes(self.sponsor),
            pack_le_uint32(self.blockHeight),
            pack_varint(_count),
            b''.join(
                (pack_varbytes(self.arbitrators[i]) for i in range(_count)))
        ))


class TxPayloadUpdateVersion(
    namedtuple("UpdateVersiion", "startHeight endHeight")):
    '''Class represeinting the Elastos Transaction Payload for Update Version'''

    def serialize(self, payload_version):
        return b''.join((
            pack_le_uint32(self.startHeight),
            pack_le_uint32(self.endHeight)
        ))


class TxPayloadCRInfo(
    namedtuple("CRInfo", "code cid did nickname url location signature")):
    '''Class representing the Elastos Transaction Payload for CR information'''

    def serialize(self, payload_version):
        return b''.join((
            self.serialize_unsigned(payload_version),
            pack_varbytes(self.signature)
        ))

    def serialize_unsigned(self, payload_version):
        return b''.join((
            pack_varbytes(self.code),
            self.cid,
            self.did if payload_version > 0 else b'',
            pack_varbytes(self.nickname),
            pack_varbytes(self.url),
            pack_le_uint64(self.location)
        ))


class TxPayloadUnregisterCR(namedtuple("UnregisterCR", "cid signature")):
    '''Class representing the Elastos Transaction Payload for unregister CR'''

    def serialize(self, payload_version):
        return b''.join((
            self.cid,
            pack_varbytes(self.signature)
        ))


class TxPayloadCRCProposal(namedtuple('CRCProposal',
                                      'type data ownerPublicKey draftHash '
                                      'budgets recipient signature did '
                                      'crSignature')):
    '''Class representing the Elastos Transaction Payload for CRC Proposal'''

    def serialize(self, payload_version):
        return b''.join((
            self.serialize_unsigned(payload_version),
            pack_varbytes(self.signature),
            self.did,
            pack_varbytes(self.crSignature)
        ))

    def serialize_unsigned(self, payload_version):
        return b''.join((
            self.type,
            pack_varbytes(self.data),
            pack_varbytes(self.ownerPublicKey),
            self.draftHash,
            pack_varint(len(self.budgets)),
            b''.join(budget.serialize() for budget in self.budgets),
            self.recipient
        ))


# Todo: test this part
class Budget(namedtuple('budget', 'type stage amount')):
    '''Class representing the CRC Proposal's budget'''

    def serialize(self):
        return b''.join((
            int_to_byte(self.type),
            int_to_byte(self.stage),
            pack_le_int64(self.amount)
        ))


# Todo: test this part
class TxPayloadCRCProposalReview(
    namedtuple('CRCProposalReview', 'hash result opinionHash did signature')):
    '''Class representing the Elastos Transaction Payload for CRC Proposal Review'''

    def serialize(self, payload_version):
        return b''.join((
            self.serialize_unsigned(payload_version),
            pack_varbytes(self.signature)
        ))

    def serialize_unsigned(self, payload_version):
        return b''.join((
            self.hash,
            int_to_byte(self.result),
            self.opinionHash,
            self.did
        ))


# Todo: test this part
class TxPayloadCRCProposalTracking(
    namedtuple('CRCProposalTracking',
               'hash messageHash stage ownerPublicKey newOwnerPublicKey '
               'ownerSignature newOwnerSignature trackingType opinionHash generalSignature')):
    '''Class representing the Elastos Transaction Payload for CRC Proposal Tracking'''

    def serialize(self, payload_version):
        return b''.join((
            self.serialize_unsigned(payload_version),
            pack_varbytes(self.ownerSignature),
            pack_varbytes(self.newOwnerSignature),
            int_to_byte(self.trackingType),
            self.opinionHash,
            pack_varbytes(self.generalSignature)
        ))

    def serialize_unsigned(self, payload_version):
        return b''.join((
            self.hash,
            self.messageHash,
            int_to_byte(self.stage),
            pack_varbytes(self.ownerPublicKey),
            pack_varbytes(self.newOwnerPublicKey)
        ))


class TxAttribute(namedtuple("TxAttribute", "usage data")):
    '''Class representing  the Elastos transaction attribute'''

    # def __str__(self):
    #     return '{usage:' + self.usage + ',data=' + self.data + '}'

    def serialize(self):
        return b''.join((
            int_to_byte(self.usage),
            pack_varbytes(self.data),
        ))


class TxInputELA(namedtuple("TxInput", "prev_hash prev_idx sequence")):
    '''Class representing an Elastos transaction input.'''

    # def __str__(self):
    #     prev_hash = hash_to_hex_str(self.prev_hash)
    #     return "Input({},{:d},sequence={:d})".format(prev_hash, self.prev_idx,
    #                                                  self.sequence)

    def is_generation(self):
        '''Test if an input is generation/coinbase like'''
        return self.prev_idx == 0xffff and self.prev_hash == ZERO and self.sequence == MINUS_1

    def serialize(self):
        return b''.join((
            self.prev_hash,
            pack_le_uint16(self.prev_idx),
            pack_le_uint32(self.sequence),
        ))


# Todo: chech wheather should add other functions
class CandidateVotes(namedtuple("CandidateVotes", "candidate votes")):
    '''Class representing the voting information for individual candidates'''

    def serialize(self, version):
        _temp = pack_varbytes(self.candidate)
        if version >= VoteProducerAndCR:
            return b''.join((
                _temp,
                pack_le_int64(self.votes)
            ))
        else:
            return _temp


# Todo: chech wheather should add other functions
class VoteContent(namedtuple("VoteContent", "vote_type candidates")):
    '''Class representing a content for voting in output_payload'''

    def serialize(self, version):
        return b''.join((
            int_to_byte(self.vote_type),  # vote type
            pack_varint(len(self.candidates)),
            b''.join(
                candidate.serialize(version) for candidate in self.candidates)
        ))


# Todo: chech wheather should add other functions
class TxOutputPayloadVote(namedtuple("OutputPayload", "version contents")):
    '''Class representing a Elastos transaction output payload used for vote.'''

    def serialize(self):
        return b''.join((
            int_to_byte(self.version),
            pack_varint(len(self.contents)),
            b''.join(
                content.serialize(self.version) for content in self.contents)
        ))


class TxOutputELA(namedtuple("TxOutput",
                             "asset_id value output_lock pk_script output_type output_payload")):
    '''Class representing an Elastos transaction output.'''

    def serialize(self, tx_version):
        _output = b''.join((
            self.asset_id,
            pack_le_int64(self.value),
            pack_le_uint32(self.output_lock),
            self.pk_script,  # uint168
        ))
        if tx_version >= 0x09:
            _output = b''.join((
                _output,
                int_to_byte(
                    self.output_type) if self.output_type is not None else b'',
                self.output_payload.serialize() if self.output_payload else b'',
            ))
        return _output


class TxScript(namedtuple("TxScript", "parameter code")):
    '''Class representing an Elastos transaction script'''

    def serialize(self):
        return b''.join((
            pack_varbytes(bytes.fromhex(self.parameter)),
            pack_varbytes(bytes.fromhex(self.code))
        ))


class TxELA(namedtuple("Tx",
                       "version type payload_version payload attributes inputs outputs locktime scripts")):
    '''Class representing Elastos transaction.'''

    def serialize_unsigned(self):
        _ser = b''
        if self.version >= 9:
            _ser = int_to_byte(self.version)
        return b''.join((
            _ser,
            int_to_byte(self.type),
            int_to_byte(self.payload_version),
            self.payload.serialize(
                self.payload_version) if self.payload else b'',
            pack_varint(len(self.attributes)),
            b''.join(attr.serialize() for attr in self.attributes),
            pack_varint(len(self.inputs)),
            b''.join(tx_in.serialize() for tx_in in self.inputs),
            pack_varint(len(self.outputs)),
            b''.join(tx_out.serialize(self.version) for tx_out in self.outputs),
            pack_le_uint32(self.locktime)
        ))

    def serialize(self):
        return b''.join((
            self.serialize_unsigned(),
            pack_varint(len(self.scripts)),
            b''.join(script.serialize() for script in self.scripts),
        ))


class DeserializerELA(DeserializerAuxPow):

    def read_tx(self):
        '''Return a deserialized ELA transaction.'''
        self.flag_byte = self._read_byte()
        if self.flag_byte >= 9:
            _version = self.flag_byte
            _type = self._read_byte()
        else:
            _version = TxVersionDefault
            _type = self.flag_byte

        _payload_version = self._read_byte()
        _payload = self._read_payload(_type, _payload_version)
        return TxELA(
            _version,  # version
            _type,  # type
            _payload_version,  # payload_version
            _payload,  # payload
            self._read_attributes(),  # attributes
            self._read_inputs(),  # inputs
            self._read_outputs(),  # outputs
            self._read_le_uint32(),  # locktime
            self._read_scripts()  # programs
        )

    # Test this part
    def _read_payload(self, tx_type, payload_version):
        read_payload = None
        if tx_type == CoinBase:
            read_payload = self._read_payload_coinbase
        elif tx_type == RegisterAsset:
            read_payload = self._read_payload_registerAsset
        elif tx_type == TransferAsset:
            read_payload = self._read_payload_transferAsset
        elif tx_type == Record:
            read_payload = self._read_payload_record
        elif tx_type == SideChainPow:
            read_payload = self._read_payload_sidechainPow
        elif tx_type == WithdrawFromSideChain:
            read_payload = self._read_payload_withdrawFromSideChain
        elif tx_type == TransferCrossChainAsset:
            read_payload = self._read_payload_transferCrossChainAsset
        elif tx_type == RegisterProducer:
            read_payload = self._read_payload_producerInfo
        elif tx_type == CancelProducer:
            read_payload = self._read_payload_processProducer
        elif tx_type == UpdateProducer:
            read_payload = self._read_payload_producerInfo
        elif tx_type == ReturnDepositCoin:
            read_payload = self._read_payload_returnDepositCoin
        elif tx_type == ActivateProducer:
            read_payload = self._read_payload_activateProducer
        elif tx_type == IllegalProposalEvidence:
            read_payload = self._read_payload_dposIllegalProposals
        elif tx_type == IllegalVoteEvidence:
            read_payload = self._read_payload_dposIllegalVotes
        elif tx_type == IllegalBlockEvidence:
            read_payload = self._read_payload_dposIllegalBlocks
        elif tx_type == IllegalSidechainEvidence:
            read_payload = self._read_payload_sidechain_illegal_data
        elif tx_type == InactiveArbitrators:
            read_payload = self._read_payload_inactive_arbitrators
        elif tx_type == UpdateVersion:
            read_payload = self._read_payload_update_version
        elif tx_type == RegisterCR:
            read_payload = self._read_payload_cr_info
        elif tx_type == UpdateCR:
            read_payload = self._read_payload_cr_info
        elif tx_type == UnregisterCR:
            read_payload = self._read_payload_UnregisterCR
        elif tx_type == ReturnCRDepositCoin:
            read_payload = self._read_payload_return_cr_deposit
        elif tx_type == CRCProposal:
            pass
        elif tx_type == CRCProposalReview:
            pass
        elif tx_type == CRCProposalTracking:
            pass
        elif tx_type == CRCAppropriation:
            pass
        elif tx_type == CRCProposalWithdraw:
            pass
        else:
            exit(-1)
        _payload = read_payload(payload_version)
        return _payload

    def _read_payload_coinbase(self, payload_version):
        return TxPayloadCoinbase(self._read_varbytes())

    def _read_payload_registerAsset(self, payload_version):
        _asset = self._read_asset()
        _amount = self._read_le_int64()
        _controller = self._read_nbytes(21)
        return TxPayloadRegisterAsset(_asset, _amount, _controller)

    def _read_asset(self):
        _name = self._read_varbytes()
        _description = self._read_varbytes()
        _precision = self._read_byte()
        _asset_type = self._read_byte()
        _record_type = self._read_byte()
        return TxAsset(_name, _description, _precision, _asset_type,
                       _record_type)

    def _read_payload_transferAsset(self, payload_version):
        # payload_transferAsset is None
        return None

    def _read_payload_record(self, payload_version):
        _type = self._read_varbytes()
        _content = self._read_varbytes()
        return TxPayloadRecord(_type, _content)

    def _read_payload_sidechainPow(self, payload_version):
        _sidechain_block_hash = self._read_nbytes(32)
        _sidechain_genesis_hash = self._read_nbytes(32)
        _height = self._read_le_uint32()
        _signature = self._read_varbytes()
        return TxPayloadSidechainPow(_sidechain_block_hash,
                                     _sidechain_genesis_hash, _height,
                                     _signature)

    def _read_payload_withdrawFromSideChain(self, payload_version):
        _height = self._read_le_uint32()
        _address = self._read_varbytes()
        read_content = self._read_nbytes
        _sidechain_tx_hashes = [read_content(32) for _ in
                                range(self._read_varint())]
        return TxPayloadWithdrawFromSidechain(_height, _address,
                                              _sidechain_tx_hashes)

    def _read_payload_transferCrossChainAsset(self, payload_version):
        _addresses = []
        _indexex = []
        _amounts = []

        _count = self._read_varint()
        for i in range(_count):
            _add = self._read_varbytes()
            _index = self._read_varint()
            _amount = self._read_le_int64()
            _addresses.append(_add)
            _indexex.append(_index)
            _amounts.append(_amount)
        return TxPayloadTransferCrosschainAsset(_addresses, _indexex, _amounts)

    def _read_payload_producerInfo(self, payload_version):
        _owner_publickey = self._read_varbytes()
        _node_publickey = self._read_varbytes()
        _nickname = self._read_varbytes()
        _url = self._read_varbytes()
        _location = self._read_le_uint64()
        _netaddress = self._read_varbytes()
        _signature = self._read_varbytes()
        return TxPayloadProducerInfo(_owner_publickey, _node_publickey,
                                     _nickname, _url, _location, _netaddress,
                                     _signature)

    def _read_payload_processProducer(self, payload_version):
        _owner_publickey = self._read_varbytes()
        _signature = self._read_varbytes()
        return TxPayloadProcessProducer(_owner_publickey, _signature)

    def _read_payload_returnDepositCoin(self, payload_version):
        # payload_returnDepositCoin is None
        return None

    def _read_payload_activateProducer(self, payload_version):
        _node_publickey = self._read_varbytes()
        _signature = self._read_varbytes()
        return TxPayloadActiveProducer(_node_publickey, _signature)

    def _read_payload_dposIllegalProposals(self, payload_version):
        _evidence = self._read_proposalEvidence()
        _compareEvidence = self._read_proposalEvidence()
        return TxPayloadDPoSIllegalProposals(_evidence, _compareEvidence)

    def _read_proposalEvidence(self):
        _proposal = self._read_dposProposal()
        _header = self._read_varbytes()
        _height = self._read_le_uint32()
        return ProposalEvidence(_proposal, _header, _height)

    def _read_dposProposal(self):
        _sponsor = self._read_varbytes()
        _blockhash = self._read_nbytes(32)
        _viewoffset = self._read_le_uint32()
        _signature = self._read_varbytes()
        return DPoSProposal(_sponsor, _blockhash, _viewoffset, _signature)

    def _read_payload_dposIllegalVotes(self, payload_version):
        _evidence = self._read_voteEvidence()
        _compareEvidence = self._read_voteEvidence()
        return TxPayloadDPoSIllegalVotes(_evidence, _compareEvidence)

    def _read_voteEvidence(self):
        _vote = self._read_dposProposalVote()
        _evidence = self._read_proposalEvidence()
        return VoteEvidence(_vote, _evidence)

    def _read_dposProposalVote(self):
        _proposalHash = self._read_nbytes(32)
        _signer = self._read_varbytes()
        _accept = self._read_byte()
        if _accept == 1:
            _accept = True
        else:
            _accept = False
        _signature = self._read_varbytes()
        return DPoSProposalVote(_proposalHash, _signer, _accept, _signature)

    def _read_payload_dposIllegalBlocks(self, payload_version):
        _coin_type, _block_height, _evidence_header, _compare_evidence_header = self._read_payload_deposIllegalBlocks_unsigned()
        _evidence_block_confirm, _evidence_signers = self._read_blockEvidence_others()
        _compare_evidence_confirm, _compare_evidence_signers = self._read_blockEvidence_others()
        return DPoSIllegalBlocks(_coin_type, _block_height,
                                 TxPayloadBlockEvidence(_evidence_header,
                                                        _evidence_block_confirm,
                                                        _evidence_signers),
                                 TxPayloadBlockEvidence(
                                     _compare_evidence_header,
                                     _compare_evidence_confirm,
                                     _compare_evidence_signers))

    def _read_payload_deposIllegalBlocks_unsigned(self):
        _coin_type = self._read_le_uint32()
        _block_height = self._read_le_uint32()
        _evidence_header = self._read_blockEvidence_unsigned()
        _compare_evidence_header = self._read_blockEvidence_unsigned()
        return _coin_type, _block_height, _evidence_header, _compare_evidence_header

    def _read_blockEvidence(self):
        _header = self._read_blockEvidence_unsigned()
        _block_confirm, _signers = self._read_blockEvidence_others()
        return TxPayloadBlockEvidence(_header, _block_confirm, _signers)

    def _read_blockEvidence_unsigned(self):
        _header = self._read_varbytes()
        return _header

    def _read_blockEvidence_others(self):
        _block_confirm = self._read_varbytes()
        _signers = [self._read_varbytes() for i in range(self._read_varint())]
        return _block_confirm, _signers

    def _read_payload_sidechain_illegal_data(self, payload_version):
        _illegalType = self._read_byte()
        _height = self._read_le_uint32()
        _illegalSigner = self._read_varbytes()
        _evidence = self._read_nbytes(32)
        _compareEvidence = self._read_nbytes(32)
        _genesisBlockAddress = self._read_varbytes()
        _signs = [self._read_varbytes() for i in range(self._read_varint())]
        return TxPayloadSidechainIllegalData(_illegalType, _height,
                                             _illegalSigner, _evidence,
                                             _compareEvidence,
                                             _genesisBlockAddress, _signs)

    def _read_payload_inactive_arbitrators(self, payload_version):
        _sponsor = self._read_varbytes()
        _blockHeight = self._read_le_uint32()
        _arbitrators = [self._read_varbytes() for i in
                        range(self._read_varint())]
        return TxPayloadInactiveArbitrators(_sponsor, _blockHeight,
                                            _arbitrators)

    def _read_payload_update_version(self, payload_version):
        _startHeight = self._read_le_uint32()
        _endHeight = self._read_le_uint32()
        return TxPayloadUpdateVersion(_startHeight, _endHeight)

    def _read_payload_cr_info(self, payload_version):
        _code = self._read_varbytes()
        _cid = self._read_nbytes(21)
        _did = None
        if payload_version > 0:
            _did = self._read_nbytes(21)
        _nickname = self._read_varbytes()
        _url = self._read_varbytes()
        _location = self._read_le_uint64()
        _signature = self._read_varbytes()
        return TxPayloadCRInfo(_code, _cid, _did, _nickname, _url, _location,
                               _signature)

    def _read_payload_UnregisterCR(self, payload_version):
        _cid = self._read_nbytes(21)
        _signature = self._read_varbytes()
        return TxPayloadUnregisterCR(_cid, _signature)

    def _read_payload_return_cr_deposit(self, payload_version):
        # payload_returnCRDepositCoin is None
        return None

    # TODO: Add the test case
    def _read_payload_crc_proposal(self, payload_version):
        _type = self._read_nbytes(2)
        _category_data = self._read_varbytes()
        _owner_pubkey = self._read_varbytes()
        _draft_hash = self._read_nbytes(32)
        read_budget = self._read_budget
        _budgets = [read_budget() for _ in range(self._read_varint())]
        _address = self._read_nbytes(21)
        _signature = self._read_varbytes()
        _did = self._read_nbytes(21)
        _cr_signature = self._read_varbytes()
        return TxPayloadCRCProposal(_type, _category_data, _owner_pubkey,
                                    _draft_hash, _budgets, _address, _signature,
                                    _did, _cr_signature)

    # Todo: Add the test case
    def _read_budget(self):
        _type = self._read_byte()
        _stage = self._read_byte()
        _amount = self._read_le_int64()
        return Budget(_type, _stage, _amount)

    # TODO: Add the test case
    def _read_payload_crc_proposal_review(self, payload_version):
        _proposalHash = self._read_nbytes(32)
        _voteResult = self._read_byte()
        _opinionHash = self._read_nbytes(32)
        _did = self._read_nbytes(21)
        _signature = self._read_varbytes()
        return TxPayloadCRCProposalReview(_proposalHash, _voteResult,
                                          _opinionHash, _did, _signature)

    # TODO: Add the test case
    def _read_payload_crc_proposal_tracking(self, payload_version):
        _proposalHash = self._read_nbytes(32)
        _messageHash = self._read_nbytes(32)
        _stage = self._read_byte()
        _ownerPublicKey = self._read_varbytes()
        _newOwnerPublicKey = self._read_varbytes()
        _ownerSignature = self._read_varbytes()
        _newOwnerSignature = self._read_varbytes()
        _trackingType = self._read_byte()
        _opinionHash = self._read_nbytes(32)
        _secretaryGeneralSignature = self._read_varbytes()
        return TxPayloadCRCProposalTracking(_proposalHash, _messageHash, _stage,
                                            _ownerPublicKey, _newOwnerPublicKey,
                                            _ownerSignature, _newOwnerSignature,
                                            _trackingType, _opinionHash,
                                            _secretaryGeneralSignature)

    # TODO: finish this part
    def _read_payload_crc_appropriation(self, payload_version):
        pass

    # TODO: finish this part
    def _read_payload_crc_proposal_withdraw(self, payload_version):
        pass

    def _read_attributes(self):
        read_attribute = self._read_attribute
        return [read_attribute() for i in range(self._read_varint())]

    def _read_attribute(self):
        _usage = self._read_byte()
        _data = self._read_varbytes()
        return TxAttribute(_usage, _data)

    def _read_input(self):
        return TxInputELA(
            self._read_nbytes(32),  # prev_hash
            self._read_le_uint16(),  # prev_idx
            self._read_le_uint32(),  # sequence
        )

    def _read_output(self):
        _asset_id = self._read_nbytes(32)  # asset_id
        _value = self._read_le_int64()  # value
        _output_lock = self._read_le_uint32()  # output_lock
        _pk_script = self._read_nbytes(21)  # pk_script
        if self.flag_byte >= 9:
            _output_type = self._read_byte()  # output_type
            _output_payload = self._read_output_payload(
                _output_type)  # output_payload
        else:
            _output_type = None
            _output_payload = None
        return TxOutputELA(
            _asset_id,
            _value,
            _output_lock,
            _pk_script,
            _output_type,
            _output_payload
        )

    def _read_output_payload(self, output_type):
        assert output_type in [0, 1]
        if output_type == 0:  # default
            return None
        if output_type == 1:  # vote
            _version = self._read_byte()
            read_content = self._read_vote_content
            # vote_content
            _contents = [read_content(_version) for _ in
                         range(self._read_varint())]
            return TxOutputPayloadVote(_version, _contents)

    def _read_vote_content(self, version):
        _vote_type = self._read_byte()
        read_canidates = self._read_candidate_votes
        _candidates = [read_canidates(version) for _ in
                       range(self._read_varint())]
        return VoteContent(_vote_type, _candidates)

    def _read_candidate_votes(self, version):
        _candidate = self._read_varbytes()
        if version >= VoteProducerAndCR:
            _votes = self._read_le_int64()
        else:
            _votes = None
        return CandidateVotes(_candidate, _votes)

    def _read_scripts(self):
        print("_read_scripts:")
        read_script = self._read_script
        return [read_script() for i in range(self._read_varint())]

    def _read_script(self):
        _parameter = bytes(self._read_varbytes()).hex()
        _code = bytes(self._read_varbytes()).hex()
        return TxScript(_parameter, _code)


'''DID Transaction'''


class DIDHeaderInfo(
    namedtuple("DIDHeaderInfo", "specification operation previoustxid")):
    '''Class representing the DID transaction payload's header'''

    def serialize(self):
        return b''.join((
            pack_varbytes(self.specification),
            pack_varbytes(self.operation),
            b'' if self.operation != b'update' else pack_varbytes(
                self.previoustxid)
        ))

    def __str__(self):
        return f'header:{self.specification}'


class DIDProofInfo(
    namedtuple("DIDProofInfo", "type verification_method signature")):
    '''Class representing the DID transaction payload's proof'''

    def serialize(self):
        return b''.join((
            pack_varbytes(self.type),
            pack_varbytes(self.verification_method),
            pack_varbytes(self.signature)
        ))


class TxPayloadDIDOperation(
    namedtuple("TxPayloadDIDOperation", "header payload proof")):
    '''Class representing the DID transaction payload for DID operation'''

    def serialize(self):
        return b''.join((
            self.header.serialize(),
            pack_varbytes(self.payload),
            self.proof.serialize()
        ))


class TxOutputDID(namedtuple("TxOutput",
                             "asset_id value output_lock pk_script")):
    '''Class representing an Elastos transaction output.'''

    def serialize(self):
        _output = b''.join((
            hex_str_to_hash(self.asset_id),
            pack_le_int64(self.value),
            pack_le_uint32(self.output_lock),
            bytes.fromhex(self.pk_script),  # uint168
        ))
        return _output


class TxDID(namedtuple("Tx",
                       "type payload_version payload attributes inputs outputs locktime scripts")):
    '''Class representing DID transaction'''

    def serialize_unsigned(self):
        return b''.join((
            int_to_byte(self.type),
            int_to_byte(self.payload_version),
            self.payload.serialize() if self.payload else b'',
            pack_varint(len(self.attributes)),
            b''.join(attr.serialize() for attr in self.attributes),
            pack_varint(len(self.inputs)),
            b''.join(tx_in.serialize() for tx_in in self.inputs),
            pack_varint(len(self.outputs)),
            b''.join(tx_out.serialize() for tx_out in self.outputs),
            pack_le_uint32(self.locktime)
        ))

    def serialize(self):
        return b''.join((
            self.serialize_unsigned(),
            pack_varint(len(self.scripts)),
            b''.join(script.serialize() for script in self.scripts),
        ))


class DeserializerDID(DeserializerELA):

    def read_tx(self):
        '''Return a deserialized DID transaction.'''
        _type = self._read_byte()
        print("type: %s " % _type)
        _version = TxVersionDefault
        print("version: %s " % _version)
        _payload_version = self._read_byte()
        print("payload version: %s " % _payload_version)
        _payload = self._read_payload(_type)
        #print("payload : %s " % _payload)
        
        return TxDID(
            _type,  # type
            _payload_version,  # payload_version
            _payload,  # payload
            self._read_attributes(),  # attributes
            self._read_inputs(),  # inputs
            self._read_outputs(),  # outputs
            self._read_le_uint32(),  # locktime
            self._read_scripts()  # programs
        )

    def _read_output(self):
        _asset_id = hash_to_hex_str(self._read_nbytes(32))  # asset_id
        _value = self._read_le_int64()  # value
        _output_lock = self._read_le_uint32()  # output_lock
        _pk_script = bytes(self._read_nbytes(21)).hex()  # pk_script
        _output_type = None
        _output_payload = None
        return TxOutputDID(
            _asset_id,
            _value,
            _output_lock,
            _pk_script,
        )

    def _read_payload(self, tx_type):
        print("in _read_payload")
        read_payload = None
        if tx_type == CoinBase:
            read_payload = self._read_payload_coinbase
        elif tx_type == RegisterAsset:
            read_payload = self._read_payload_registerAsset
        elif tx_type == TransferAsset:
            read_payload = self._read_payload_transferAsset
        elif tx_type == Record:
            read_payload = self._read_payload_record
        elif tx_type == SideChainPow:
            read_payload = self._read_payload_sidechainPow
        elif tx_type == WithdrawFromSideChain:
            read_payload = self._read_payload_withdrawFromSideChain
        elif tx_type == TransferCrossChainAsset:
            read_payload = self._read_payload_transferCrossChainAsset
        elif tx_type == RegisterDID:
            read_payload = self._read_payload_did_operation
        else:
            print("Error in _read_payload")
            exit(-1)
        _payload = read_payload()
        return _payload

    def _read_did_operation_header(self):
        _spec = self._read_varbytes()
        _op = self._read_varbytes()
        _txid = b'' if _op != b'update' else self._read_varbytes()
        return DIDHeaderInfo(_spec, _op, _txid)

    def _read_did_operation_proof(self):
        _type = self._read_varbytes()
        _verification_method = self._read_varbytes()
        _signature = self._read_varbytes()
        return DIDProofInfo(_type, _verification_method, _signature)

    def _read_payload_did_operation(self):
        _header = self._read_did_operation_header()
        _payload = self._read_varbytes()
        _proof = self._read_did_operation_proof()
        return TxPayloadDIDOperation(_header, _payload, _proof)






