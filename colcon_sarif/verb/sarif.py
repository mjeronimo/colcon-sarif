# Copyright 2016-2019 Dirk Thomas
# Licensed under the Apache License, Version 2.0

import argparse
from contextlib import suppress
import os
import sys

from colcon_core.logging import colcon_logger
from colcon_core.plugin_system import satisfies_version
from colcon_core.verb import VerbExtensionPoint
from process_sarif.sarif_helpers import get_sarif_in_build, find_duplicate_results, replace_misra_results
from process_sarif.visualize import main as gen_images

logger = colcon_logger.getChild(__name__)


class TestResultVerb(VerbExtensionPoint):
    """Show the test results generated when testing a set of packages."""

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
            '--all',
            action='store_true',
            help='Show all test result files (even without errors / failures)')
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show additional information for each error / failure')
        parser.add_argument(
            '--gen-images',
            action='store_true',
            help='Generate images')
        parser.add_argument(
            '--result-files-only',
            action='store_true',
            help='Print only the paths of the result files. '
                 'Use with --all to include files without errors / failures')
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete all result files. This might include additional '
                 'files beside what is listed by --result-files-only. An '
                 'interactive prompt will ask for confirmation')
        parser.add_argument(
            '--delete-yes',
            action='store_true',
            help='Same as --delete without an interactive confirmation')

    def main(self, *, context):  # noqa: D102

        all_files = set() \
            if (context.args.delete or context.args.delete_yes) else None

        # TODO:
        #   use context.args.base_dir
        #   provide log_path on command line

        all_results = get_sarif_in_build(verbose=context.args.verbose, log_path="logfile.txt")

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

        results = [
            r for r in all_results
            if len(r._results) or context.args.all]
        #results.sort(key=lambda r: r.path)

        if context.args.result_files_only:
            for result in results:
                print(result.path)

        if context.args.gen_images:
            gen_images()
            return

        #else:
        #    for result in results:
        #        print(result)
        #        if context.args.verbose:
        #            for detail in result.details:
        #                for i, line in enumerate(detail.splitlines()):
        #                    print('-' if i == 0 else ' ', line)

        #summary = Result('Summary')
        #for result in all_results:
        #    summary.add_result(result)

        #if not context.args.result_files_only:
        #    if results:
        #        print()
        #    print(summary)

        #return 1 if summary.error_count or summary.failure_count else 0
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
