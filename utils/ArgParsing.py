#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2022 Qumulo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
# ArgParsing.py
#

# Import Python system libraries
import sys
import argparse

from utils.Logger import Logger

# Define the name of the Program, Description, and Version.
progname = "DirectoryTrends"
progdesc = "Qumulo DirectoryTrends - Show the capacity changes of the defined directories daily and weekly basis."
progvers = "6.1.0"

# Start by getting any command line arguments
def parse_args(parser, commands):
    # Divide argv by commands
    split_argv = [[]]
    for c in sys.argv[1:]:
        if c in commands.choices:
            split_argv.append([c])
        else:
            split_argv[-1].append(c)
    # Initialize namespace
    args = argparse.Namespace()
    for c in commands.choices:
        setattr(args, c, None)
    # Parse each command
    parser.parse_args(split_argv[0], namespace=args)  # Without command
    for argv in split_argv[1:]:  # Commands
        n = argparse.Namespace()
        setattr(args, argv[0], n)
        parser.parse_args(argv, namespace=n)
    return args


def main():
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version=f"{progname} - Version {progvers}",
        )
        parser.add_argument(
            "-l",
            "--log",
            default="INFO",
            required=False,
            dest="loglevel",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            help="Set the logging level."
        )
        parser.add_argument(
            "-c",
            "--config-file",
            dest="config_file",
            default = "",
            help="The configuration file which has the definitions of how to run this script"
        )



        commands = parser.add_subparsers(title="sub-commands")

        # Create a subcommand parser for the "directories" subcommand
        smb_parser = commands.add_parser("directories", help="Define the details of the directories which will be checked")
        smb_parser.add_argument(
            "-d",
            "--dir-paths",
            dest="dir_paths",
            nargs="+",
            default=[""],
            help="Directory path to check",
        )
        smb_parser.add_argument(
            "--max-depth",
            dest="max_depth",
            default=0,
            help="Maximum depth",
        )

        # Create a subcommand parser for the "cluster" subcommand
        src_parser = commands.add_parser("cluster", help="Qumulo cluster details")
        src_parser.add_argument(
            "--address",
            dest="address",
            default="",
            help="Qumulo cluster IP address or hostname",
        )
        src_parser.add_argument(
            "--port",
            dest="cluster_port",
            default=8000,
            help="Qumulo cluster port number",
        )
        src_parser.add_argument(
            "--username",
            dest="username",
            default="",
            help="Source Qumulo cluster username",
        )
        src_parser.add_argument(
            "--password",
            dest="password",
            default="",
            help="Source Qumulo cluster password",
        )
        src_parser.add_argument(
            "--access-token",
            dest="access_token",
            default="",
            help="Source Qumulo cluster access token",
        )

        # Create a subcommand parser for the "email" subcommand
        dst_parser = commands.add_parser(
            "email", help="Email details"
        )
        dst_parser.add_argument(
            "--from",
            dest="email_from",
            default="",
            help="From address for email",
        )
        dst_parser.add_argument(
            "--to",
            dest="email_to",
            default="",
            help="To address for email",
        )
        dst_parser.add_argument(
            "--login",
            dest="login",
            default="",
            help="SMTP server login user",
        )
        dst_parser.add_argument(
            "--password",
            dest="password",
            default="",
            help="SMTP server password",
        )
        dst_parser.add_argument(
            "--server",
            dest="server",
            default="",
            help="SMTP server IP address or hostname",
        )
        dst_parser.add_argument(
            "--port",
            dest="port",
            default=25,
            help="SMTP server port number",
        )
        dst_parser.add_argument(
            "--use",
            dest="use",
            default="none",
            help="SMTP server TLS, SSL, none",
        )


        args = parse_args(parser, commands)
        
        return args

    except argparse.ArgumentTypeError:
        # Log an error
        sys.exit(1)

    # Build a logger to handle logging events.
    logger = Logger(name=progname, version=progvers, level=args.loglevel, log_path=None)


if __name__ == "__main__":
    main()
