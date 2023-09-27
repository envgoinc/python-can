import sys
import os
import argparse
from datetime import datetime
import errno
from typing import Any, Dict, List, Union, Sequence, Tuple
from random import randint

import can
from can import Message
from can.io import BaseRotatingLogger
from can.io.generic import MessageWriter
from can.util import cast_from_string
from . import Logger
from .typechecking import CanFilter, CanFilters


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate CAN log file")

    parser.add_argument(
        "-a",
        "--append",
        dest="append",
        help="Append to the log file if it already exists.",
        action="store_true",
    )

    parser.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="""How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG""",
        default=2,
    )

    parser.add_argument(
        "outfile",
        metavar="out-file",
        type=str,
        help="The file to generate. For supported types see can.LogReader.",
    )

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    results, unknown_args = parser.parse_known_args()

    print(f"Generating log (Started on {datetime.now()})")

    logger: Union[MessageWriter, BaseRotatingLogger]
    logger = Logger(
        filename=results.outfile,
        append=results.append,
    )

    for _ in range(10000):
        msg = Message(arbitration_id=randint(0, 300), channel=0, is_extended_id=False, is_rx=False, data=bytearray(os.urandom(randint(1, 8))))
        logger(msg)

    logger.stop()


if __name__ == "__main__":
    main()
