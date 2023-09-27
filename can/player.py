"""
Replays CAN traffic saved with can.logger back
to a CAN bus.

Similar to canplayer in the can-utils package.
"""

import sys
import time
import argparse
from datetime import datetime
import errno
from typing import cast, Iterable

from can import LogReader, Message, MessageSync

from .logger import _create_base_argument_parser, _create_bus, _parse_additional_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay CAN traffic.")

    _create_base_argument_parser(parser)

    parser.add_argument(
        "-f",
        "--file_name",
        dest="log_file",
        help="Path and base log filename, for supported types see can.LogReader.",
        default=None,
    )

    parser.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="""Also print can frames to stdout.
                        You can add several of these to enable debugging""",
        default=2,
    )

    parser.add_argument(
        "--ignore-timestamps",
        dest="timestamps",
        help="""Ignore timestamps (send all frames immediately with minimum gap between frames)""",
        action="store_false",
    )

    parser.add_argument(
        "--error-frames",
        help="Also send error frames to the interface.",
        action="store_true",
    )

    parser.add_argument(
        "--loopback-test",
        dest="test",
        help="Also receive messages and check that what was sent is received.",
        action="store_true",
    )

    parser.add_argument(
        "-g",
        "--gap",
        type=float,
        help="<s> minimum time between replayed frames",
        default=0.0001,
    )
    parser.add_argument(
        "-s",
        "--skip",
        type=float,
        default=60 * 60 * 24,
        help="<s> skip gaps greater than 's' seconds",
    )

    parser.add_argument(
        "infile",
        metavar="input-file",
        type=str,
        help="The file to replay. For supported types see can.LogReader.",
    )

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    results, unknown_args = parser.parse_known_args()
    additional_config = _parse_additional_config([*results.extra_args, *unknown_args])

    verbosity = results.verbosity

    error_frames = results.error_frames
    test = results.test

    with _create_bus(results, **additional_config) as bus:
        with LogReader(results.infile, **additional_config) as reader:

            in_sync = MessageSync(
                cast(Iterable[Message], reader),
                timestamps=results.timestamps,
                gap=results.gap,
                skip=results.skip,
            )

            print(f"Can LogReader (Started on {datetime.now()})")

            try:
                errors = 0
                # flush receive buffer
                if test:
                    while bus.recv(0.1) is not None:
                        pass
                for message in in_sync:
                    if message.is_error_frame and not error_frames:
                        continue
                    if verbosity >= 3:
                        print(message)

                    bus.send(message)
                    if(test):
                        recv_msg = bus.recv(2)
                        if recv_msg is None:
                            print(f"Didn't get message: {message}")
                        elif not((recv_msg.arbitration_id == message.arbitration_id) and
                           (recv_msg.data == message.data)):
                            print("Messages don't match.")
                            print(f"sent:    {message}")
                            print(f"received:{recv_msg}")
                            errors += 1
                        time.sleep(0.005)
                    else:
                        recv_msg = bus.recv(0.1)
                        if recv_msg is not None:
                            print(f"received {recv_msg.arbitration_id}")

            except KeyboardInterrupt:
                pass
            finally:
                if bus.total_messages != 0:
                    error_pct = errors/bus.total_messages * 100
                else:
                    error_pct = 0
                if bus.get_uptime() != 0:
                    bus_utilization_percentage = bus.total_data * 100 / (bus._bitrate / 8 * bus.get_uptime())
                else:
                    bus_utilization_percentage = 0
                print(f"Error rate: {error_pct}, total messages: {bus.total_messages}")
                print(f"Bus usage = {bus_utilization_percentage:.2f}%")


if __name__ == "__main__":
    main()
