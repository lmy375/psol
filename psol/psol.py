import asyncio
import json

import requests
from anchorpy import Idl, Program, Provider
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature

from .idl import IdlDatabase
from .utils import to_dict

RPC_URL = {
    "mainnet": "https://api.mainnet-beta.solana.com",
    "testnet": "https://api.testnet.solana.com",
    "devnet": "https://api.devnet.solana.com",
}


class Psol(object):

    def __init__(self, cluster="mainnet", rpc_url=None) -> None:
        assert cluster in RPC_URL, f"Cluster {cluster} not supported"
        self.cluster = cluster

        if not rpc_url:
            rpc_url = RPC_URL[cluster]

        self.provider = Provider.local(rpc_url)
        self.client = Client(rpc_url)

        self.idl_db = IdlDatabase()

    def fetch_idl_onchain(self, program_id: str) -> str:
        async def _fetch(program_id: str) -> str:
            idl = await Program.fetch_raw_idl(program_id, self.provider)
            return idl

        return asyncio.run(_fetch(program_id))

    def fetch_idl_solscan(self, program_id: str) -> str:
        assert self.cluster == "mainnet", "Only support mainnet"

        r = requests.get(
            f"https://api-v2.solscan.io/v2/account/anchor_idl?address={program_id}",
            headers={
                "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
                "Origin": "https://solscan.io",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "accept": "application/json, text/plain, */*",
            },
        )
        resp = r.json()
        assert resp["success"], "Solscan API failed"
        return json.dumps(resp["data"])

    def fetch_idl_explorer(self, program_id: str) -> str:
        assert self.cluster == "mainnet", "Only support mainnet"

        r = requests.get(
            f"https://explorer.solana.com/api/anchor?programAddress={program_id}&cluster=0",
            headers={
                "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
                "Origin": "https://explorer.solana.com",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "accept": "application/json, text/plain, */*",
            },
        )
        resp = r.json()
        return json.dumps(resp["idl"])

    def fetch_idl(self, program_id: str) -> tuple[str, str | None]:

        idl = self.idl_db.get_idl(self.cluster, program_id)
        if idl:
            return "local", idl

        def _get_idl():
            try:
                idl = self.fetch_idl_explorer(program_id)
                return "explorer", idl
            except Exception:
                pass

            try:
                idl = self.fetch_idl_solscan(program_id)
                return "solscan", idl
            except Exception:
                pass

            return "NotFound", None

        typ, idl = _get_idl()
        if idl:
            self.idl_db.save_idl(self.cluster, program_id, idl)
            return typ, idl

        return "NotFound", None

    def set_cluster(self, cluster: str):
        assert cluster in RPC_URL, f"Cluster {cluster} not supported"
        rpc_url = RPC_URL[cluster]
        self.provider = Provider.local(rpc_url)
        self.client = Client(rpc_url)

    def get_account_info(self, _pubkey: str) -> tuple[dict, dict]:
        pubkey = Pubkey.from_string(_pubkey)
        account = self.client.get_account_info(pubkey).value
        assert account, f"Account not found: {pubkey}"

        acc_dict = json.loads(account.to_json())
        acc_dict["data"] = account.data[:100].hex()
        size = len(account.data)
        if size > 100:
            acc_dict["data"] += "..."
        acc_dict["size"] = size

        discriminator = account.data[:8].hex()
        idl_str, name = self.idl_db.load_idl_by_account_discriminator(discriminator)
        parsed_data = {}
        if idl_str:
            idl = Idl.from_json(idl_str)

            async def _fetch_acc():
                program = Program(idl, pubkey, self.provider)
                return await program.account[name].fetch(pubkey)

            parsed_data = asyncio.run(_fetch_acc()).__dict__

        if not parsed_data:
            acc = self.client.get_account_info_json_parsed(pubkey).value
            if acc:
                data = acc.data
                if not isinstance(data, bytes):
                    parsed_data = json.loads(data.to_json())

        return acc_dict, parsed_data

    def get_account_name(self, pubkey: str) -> str:
        assert self.cluster == "mainnet", "Only support mainnet"

        if pubkey in self.idl_db.names:
            return self.idl_db.names[pubkey]

        try:
            r = requests.get(
                f"https://api-v2.solscan.io/v2/account?address={pubkey}",
                headers={
                    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
                    "Origin": "https://solscan.io",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    "accept": "application/json, text/plain, */*",
                },
            )
            resp = r.json()
            assert resp["success"], "Solscan API failed"
            name = resp["data"]["notifications"]["label"]
            if name:
                self.idl_db.names[pubkey] = name
                return name
        except Exception:
            pass

        try:
            r = requests.post(
                "https://api.solana.fm/v0/accounts",
                headers={
                    "content-type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    "accept": "application/json",
                },
                json={"accountHashes": [pubkey]},
            )
            resp = r.json()
            assert resp["status"] == "Success", "solana.fm API failed"
            name += resp["result"][0]["data"]["friendlyName"]
            if name:
                self.idl_db.names[pubkey] = name
                return name
        except Exception:
            pass

        return "Unknown"

    def get_transaction(self, signature: str) -> dict:
        tx_sig = Signature.from_string(signature)
        tx = self.client.get_transaction(
            tx_sig, max_supported_transaction_version=100
        ).value
        assert tx, f"Transaction not found: {tx_sig}"
        tx_dict = json.loads(tx.to_json())
        return tx_dict

    def decode_ix_data(self, ix_data: str) -> dict:

        discriminator = ix_data[:16]
        idl_str, name = self.idl_db.load_idl_by_instruction_discriminator(discriminator)
        if not idl_str:
            return {"error": f"Unknow discriminator {discriminator}"}

        idl = Idl.from_json(idl_str)
        program = Program(idl, Pubkey.default(), self.provider)

        ix_bytes = bytes.fromhex(ix_data)
        ix_parsed = program.coder.instruction.parse(ix_bytes)

        return to_dict(ix_parsed)
