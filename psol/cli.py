from argparse import ArgumentParser

from .console import PsolConsole
from .psol import Psol


def get_args():
    parser = ArgumentParser(
        prog="psol", description="A solana command-line tool written in python."
    )

    parser.add_argument(
        "-c",
        "--cluster",
        choices=["mainnet", "devnet", "testnet"],
        default="mainnet",
        help="Solana network.",
    )

    parser.add_argument(
        "-u",
        "--rpc-url",
        help="RPC endpoint.",
    )

    parser.add_argument(
        "--cmd",
        nargs="+",
        help="Execute one command in peth console.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug logs.",
    )

    args = parser.parse_args()
    return args


def main():
    args = get_args()

    psol = Psol(args.cluster, args.rpc_url)
    console = PsolConsole(psol)

    if args.debug:
        console._debug = True

    if args.cmd:
        cmd_str = " ".join(args.cmd)
        for cmd in cmd_str.split(";"):
            console.single_command(cmd)
    else:
        console.start_console()


if __name__ == "__main__":
    main()
