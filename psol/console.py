import base64
import cmd
import json
import os
import urllib

import base58
import requests
from solders.message import Message
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction import VersionedTransaction

from .psol import Psol
from .utils import SolanaJSONEncoder


class PsolConsole(cmd.Cmd):

    prompt = "psol > "

    def __init__(self, psol: Psol) -> None:
        super().__init__()
        self.psol: Psol = psol

        self._debug = False

    @property
    def client(self):
        return self.psol.client

    def _normal_str(self, v, full=False):
        if isinstance(v, bytes):
            v = v.hex()
        v = str(v).splitlines()[0]
        if not full and len(v) > 80:
            v = v[:80] + " ..."
        return v

    def _print_json(self, data, full=False):
        if isinstance(data, list):
            i = 1
            for item in data:
                print("---- [%d] ----" % i)
                self._print_json(item, full)
                i += 1
        elif getattr(data, "items", None):  # dict-like object.
            for k, v in data.items():
                if v:
                    v = self._normal_str(v, full)
                print(" ", k, ":\t", v)
        else:
            print(self._normal_str(data, full))

    def _decode_hex_or_base64(self, s: str) -> bytes:
        try:
            return bytes.fromhex(s)
        except Exception:
            return base64.b64decode(s)

    def onecmd(self, line):
        try:
            # ! run system shell.
            # ? eval python script.
            if line.startswith("!"):
                line = "sh " + line[1:]
            elif line.startswith("?"):
                line = "py " + line[1:]

            return super().onecmd(line)
        except Exception as e:
            print("Error: ", e)
            if self._debug:
                raise Exception from e

            cmd = line.split()[0]
            super().onecmd(f"help {cmd}")
            return False  # don't stop

    def start_console(self):
        """
        Start a console. Catch Ctrl+C.
        """

        print("Welcome to the psol shell. Type `help` to list commands.\n")
        while True:
            try:
                self.cmdloop()
                return
            except KeyboardInterrupt:
                print()  # new line.

    def single_command(self, cmd, debug=True):
        """
        Run single command. This will not catch call exception by default.
        """
        if type(cmd) is list:
            cmd = " ".join(cmd)
        else:
            cmd = str(cmd)

        self._debug = debug
        self.onecmd(cmd)

    def do_sh(self, arg):
        """
        sh <cmd>: Run system shell command.
        """
        os.system(arg)

    def do_py(self, arg):
        """
        py <expr>: Eval python script.
        """
        print(eval(arg.strip()))

    def do_open(self, arg):
        """
        open <path>: Open url or file.
        """
        self.do_sh("open " + arg)

    def do_exit(self, arg):
        """
        exit: Exit the console.
        """

        print("bye!")
        return True

    def do_ipython(self, arg=None):
        """
        ipython: Open ipython console
        """
        __import__("IPython").embed(colors="Linux")

    def do_base58(self, arg: str):
        """
        base58 enc <hex>: Encode into base58
        base58 dec <base58>: Decode base58
        """
        op, text = arg.split()
        if op == "enc":
            if text.startswith("0x"):
                text = text[2:]
            data = bytes.fromhex(text)
            print(f"Data Length: {len(data)} bytes")
            print(f"Base58: {base58.b58encode(data).decode()}")
            print(f"Base58Check: {base58.b58encode_check(data).decode()}")
        else:
            assert op == "dec"
            try:
                data = base58.b58decode_check(text)
                print("Base58 with check:")
                print(f"  Data Length: {len(data)} bytes")
                print(f"  Hex: {data.hex()}")
            except Exception:
                pass

            data = base58.b58decode(text)
            print("Base58:")
            print(f"  Data Length: {len(data)} bytes")
            print(f"  Hex: {data.hex()}")

    def do_cluster(self, cluster: str):
        """
        cluster <cluster>: Change cluster.
        """
        self.psol.set_cluster(cluster)
        print(f"Cluster set to {cluster}")

    def do_fetch_idl(self, arg: str):
        """
        fetch_idl <program_id>: Fetch IDL from solscan and onchain.
        """
        program_id = arg.strip()
        src, idl = self.psol.fetch_idl(program_id)
        if idl is None:
            print(f"IDL not found for {program_id}")
            return

        name = json.loads(idl)["metadata"]["name"]

        print(f"IDL {name} found for {program_id} from {src}")

    def do_local_idl(self, file_path: str):
        """
        local_idl <file_path>: Load IDL from local file.
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        idl = open(file_path).read()
        name = json.loads(idl)["metadata"]["name"]
        print(f"IDL {name} loaded from {file_path}")
        path = self.psol.idl_db.save_idl("local", name, idl)
        print(f"Saved to {path}")

    def do_account(self, pubkey: str):
        """
        account <pubkey>: Load account info.
        """
        account, parsed = self.psol.get_account_info(pubkey)
        print(json.dumps(account, indent=2, cls=SolanaJSONEncoder))
        if parsed:
            print("---- Parsed ----")
            print(json.dumps(parsed, indent=2, cls=SolanaJSONEncoder))

    def do_name(self, pubkey: str):
        """
        name <pubkey>: Get account name
        """
        name = self.psol.get_account_name(pubkey)
        print(name)

    def do_tx(self, tx_sig: str):
        """
        tx <sig>: Print tx info.
        """
        tx = self.psol.get_transaction(tx_sig)
        print(json.dumps(tx, indent=2, cls=SolanaJSONEncoder))

    def do_tx_base64(self, tx_sig: str):
        """
        tx_base64: Print tx base64 bytes.
        """
        tx_sig = Signature.from_string(tx_sig)
        resp = self.client.get_transaction(
            tx_sig, max_supported_transaction_version=100, encoding="base64"
        ).value
        base64_data = base64.b64encode(
            bytes(resp.transaction.transaction.message)
        ).decode()
        print(base64_data)

    def do_inspect(self, base64_data: str):
        """
        inspect <tx_sig>:  Inspect from tx signature.
        inspect <base64_data>:  Inspect from base64 tx data.
        """
        try:
            tx_sig = Signature.from_string(base64_data)
            resp = self.client.get_transaction(
                tx_sig, max_supported_transaction_version=100, encoding="base64"
            ).value
            base64_data = base64.b64encode(
                bytes(resp.transaction.transaction.message)
            ).decode()
        except Exception:
            pass

        url = f"https://explorer.solana.com/tx/inspector?message={urllib.parse.quote(base64_data)}"
        print(url)
        self.do_open(url)

    def do_ix_decode(self, ix_data: str):
        """
        ix_decode <data>: Decode ix data (hex or base64).
        """
        data = self._decode_hex_or_base64(ix_data)
        decoded = self.psol.decode_ix_data(data.hex())
        print(json.dumps(decoded, indent=2, cls=SolanaJSONEncoder))

    def do_tx_decode(self, tx_data: str):
        """
        tx_decode <tx_data>: Decode tx data (hex or base64).
        """
        data = self._decode_hex_or_base64(tx_data)
        tx = VersionedTransaction.from_bytes(data)
        print(repr(tx))

        try:
            tx.sanitize()
            print("\n---- Transaction is valid ----")
        except Exception as e:
            print("\n---- Transaction is invalid ----")
            print("Sanitization error:", e)

    def do_tx_simulate(self, tx_data: str):
        """
        tx_simulate <tx_data>: Simulate tx data (hex or base64).
        """
        data = self._decode_hex_or_base64(tx_data)

        url = self.client._provider.endpoint_uri
        resp = requests.post(
            url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "simulateTransaction",
                "params": [
                    base64.b64encode(data).decode(),
                    {
                        "encoding": "base64",
                        "sigVerify": False,
                        "replaceRecentBlockhash": True,
                    },
                ],
            },
            headers={"Content-Type": "application/json"},
        )
        value = resp.json()["result"]["value"]
        print(json.dumps(value, indent=2))

        # tx = VersionedTransaction.from_bytes(data)
        # resp = self.client.simulate_transaction(tx, sig_verify=False)
        # print(repr(resp.value))

    def do_msg_decode(self, msg_data: str):
        """
        msg_decode <msg_data>: Decode message data
        """
        data = self._decode_hex_or_base64(msg_data)
        msg = Message.from_bytes(data)
        print(repr(msg))

    def do_pda(self, arg_str: str):
        """
        pda <program_id> [<pubkey|hex|string>, ..]: Find program address.
        """
        args = arg_str.split()
        program_id = Pubkey.from_string(args[0])
        seeds = []
        for value in args[1:]:
            try:
                pubkey = Pubkey.from_string(value)
                seeds.append(bytes(pubkey))
                continue
            except ValueError:
                pass

            try:
                seeds.append(bytes.fromhex(value))
                continue
            except ValueError:
                pass

            seeds.append(bytes(value, "utf-8"))

        pda, bump = Pubkey.find_program_address(seeds, program_id)
        print("PDA:", pda)
        print("Bump:", bump)
