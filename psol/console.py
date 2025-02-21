import cmd
import json
import os

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
        Run system shell command.
        """
        os.system(arg)

    def do_py(self, arg):
        """
        Eval python script.
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

        __import__("IPython").embed(colors="Linux")

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

        print(f"IDL found for {program_id} from {src}")

    def do_local_idl(self, file_path: str):
        """
        local_idl <file_path>: Load IDL from local file.
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        idl = open(file_path).read()
        print(f"IDL loaded from {file_path}")

        name = json.loads(idl)["name"]
        path = self.psol.idl_db.save_idl("local", name, idl)
        print(f"Saved to {path}")

    def do_account(self, pubkey: str):
        account, parsed = self.psol.get_account_info(pubkey)
        print(json.dumps(account, indent=2, cls=SolanaJSONEncoder))
        if parsed:
            print("---- Parsed ----")
            print(json.dumps(parsed, indent=2, cls=SolanaJSONEncoder))

    def do_tx(self, tx_sig: str):
        tx = self.psol.get_transaction(tx_sig)
        print(json.dumps(tx, indent=2, cls=SolanaJSONEncoder))

    def do_ix_decode(self, ix_data: str):
        decoded = self.psol.decode_ix_data(ix_data)
        print(json.dumps(decoded, indent=2, cls=SolanaJSONEncoder))
