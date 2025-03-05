import atexit
import json
import pathlib
from hashlib import sha256

HOME = pathlib.Path().home()
PSOL_DATA = HOME / ".psol"
IDL_CACHE = PSOL_DATA / "idl_cache"

ACCOUNTS_IDL = PSOL_DATA / "accounts_idl.json"
INSTRUCTIONS_IDL = PSOL_DATA / "instructions_idl.json"
TYPES_IDL = PSOL_DATA / "types_idl.json"
NAMES = PSOL_DATA / "names.json"

if not ACCOUNTS_IDL.parent.exists():
    ACCOUNTS_IDL.parent.mkdir(parents=True)

if not INSTRUCTIONS_IDL.parent.exists():
    INSTRUCTIONS_IDL.parent.mkdir(parents=True)

if not NAMES.parent.exists():
    NAMES.parent.mkdir(parents=True)


class IdlDatabase(object):

    def __init__(self) -> None:
        if not ACCOUNTS_IDL.exists():
            self.accounts = {}
        else:
            self.accounts = json.loads(ACCOUNTS_IDL.read_text())

        if not INSTRUCTIONS_IDL.exists():
            self.instructions = {}
        else:
            self.instructions = json.loads(INSTRUCTIONS_IDL.read_text())

        if not NAMES.exists():
            self.names = {}
        else:
            self.names = json.loads(NAMES.read_text())

        atexit.register(self.save)

    def save(self):
        ACCOUNTS_IDL.write_text(json.dumps(self.accounts, indent=2))
        INSTRUCTIONS_IDL.write_text(json.dumps(self.instructions, indent=2))
        NAMES.write_text(json.dumps(self.names, indent=2))

    def save_idl(self, cluster: str, program_id: str, idl: str) -> str:

        dir = IDL_CACHE / cluster

        if not dir.exists():
            dir.mkdir(parents=True)

        path = dir / f"{program_id}.json"
        path.write_text(idl)
        self.index_idl(idl, str(path))
        return str(path)

    def get_idl(self, cluster: str, program_id: str) -> str | None:
        try:
            idl_path = IDL_CACHE / cluster / f"{program_id}.json"
            return idl_path.read_text()
        except FileNotFoundError:
            return None

    def load_idl(self, cluster: str, program_id: str) -> str | None:
        try:
            idl_path = IDL_CACHE / cluster / f"{program_id}.json"
            return idl_path.read_text()
        except FileNotFoundError:
            return None

    def _account_discriminator(self, name: str) -> str:
        return sha256(f"account:{name}".encode()).digest()[:8].hex()

    def _instruction_discriminator(self, name: str) -> str:
        return sha256(f"global:{name}".encode()).digest()[:8].hex()

    def index_idl(self, idl_str: str, path: str):
        idl = json.loads(idl_str)
        for account in idl.get("accounts", []):
            name = account["name"]
            discriminator = self._account_discriminator(name)
            self.accounts[discriminator] = [path, name]

        for instruction in idl.get("instructions", []):
            name = instruction["name"]
            discriminator = self._instruction_discriminator(name)
            self.instructions[discriminator] = [path, name]

    def load_idl_by_account_discriminator(self, discriminator: str) -> tuple[str, str]:
        if discriminator not in self.accounts:
            return "", ""

        path, name = self.accounts[discriminator]
        return open(path).read(), name

    def load_idl_by_instruction_discriminator(
        self, discriminator: str
    ) -> tuple[str, str]:
        if discriminator not in self.instructions:
            return "", ""

        path, name = self.instructions[discriminator]
        return open(path).read(), name
