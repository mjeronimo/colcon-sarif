# Copyright 2016-2019 Dirk Thomas
# Licensed under the Apache License, Version 2.0

import argparse
from contextlib import suppress
import os
import sys

from colcon_core.plugin_system import satisfies_version
from colcon_core.verb import VerbExtensionPoint
from process_sarif.sarif_helpers import \
    get_sarif_in_build, find_duplicate_results, replace_misra_results
from process_sarif.visualize import main as gen_images


class SarifVerb(VerbExtensionPoint):
    """Display information from SARIF files."""

    __test__ = False  # prevent the class from being identified as a test

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(VerbExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            '--base-dir',
            type=_argparse_existing_dir,
            default='build',
            help='The directory in which to find the SARIF files (default: build)')
        parser.add_argument(
            '--bundle',
            action='store_true',
            help='Bundle the SARIF files into a single tarball with metadata')
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete all SARIF files. An interactive prompt will ask for confirmation')
        parser.add_argument(
            '--delete-yes',
            action='store_true',
            help='Same as --delete without an interactive confirmation')
        parser.add_argument(
            '--gen-images',
            action='store_true',
            help='Generate images')
        parser.add_argument(
            '--print-filenames',
            action='store_true',
            help='Print only the paths of the SARIF files')
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show additional information for each issue')

    def main(self, *, context):  # noqa: D102

        # TODO:
        #   use context.args.base_dir
        #   provide log_path on command line
        (sarif_filenames, sarif_files) = get_sarif_in_build(verbose=context.args.verbose, log_path="logfile.txt")

        all_files = sorted(sarif_filenames)

        if context.args.delete or context.args.delete_yes:
            if not all_files:
                print('No result files found to delete')
                return 0
            for path in sorted(all_files):
                print('-', path)
            while not context.args.delete_yes:
                response = _safe_input(
                    'Delete these %d files? [y/n] ' % len(all_files))
                if response.lower() == 'y':
                    break
                if response.lower() == 'n':
                    print('Aborted')
                    return 0
            for path in sorted(all_files):
                os.remove(path)
            print('Deleted %d files' % len(all_files))
            return 0

        if context.args.print_filenames:
            for filename in sarif_filenames:
                print(os.path.relpath(filename, os.getcwd()))
            return 0

        if context.args.gen_images:
            gen_images()
            return 0

        return 0


def _argparse_existing_dir(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("Path '%s' does not exist" % path)
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError("Path '%s' is not a directory" % path)
    return path


def _safe_input(prompt=None):
    # flush stdin before checking for input
    # skip if not supported on some platforms
    with suppress(ImportError):
        from termios import tcflush
        from termios import TCIFLUSH
        tcflush(sys.stdin, TCIFLUSH)
    return input(prompt)
