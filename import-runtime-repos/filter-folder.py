#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapper for git-filter-repo to extract paths into a new clone, following the
rename history to preserve all revisions of whitelisted paths.

WARNING: There appears to be no way to ask git-filter-repo to exclude stuff
         that later takes on a name a renamed file gave up, so this will be
         insufficient if you move a/b.py to b/b.py and then create a new a/b.py
         and only want to preserve the history of b/b.py without keeping the
         unrelated a/b.py.
"""

# git filter-repo --to-subdirectory-filter cumulus
# python ../remove-folder.py cumulus/parachain2

__appname__ = "git-extract-paths-with-history"
__authors__ = "Stephan Sokolow (deitarion/SSokolow)"
__version__ = "0.1"
__license__ = "MIT"

import logging, os, shlex, sys, tempfile
import subprocess  # nosec
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from typing import List

log = logging.getLogger(__name__)
fs_encoding = sys.getfilesystemencoding()


def get_git_root(path: str = None) -> str:
    """Get the root path of the git repository at the given path

    Will use the current working directory if `None` and will raise
    subprocess.CalledProcessError on failure.
    """
    return subprocess.check_output(  # nosec
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=path, stderr=subprocess.DEVNULL).strip()


def get_path_history(path: List[str]) -> List[str]:
    """Expand a path into all the names it's taken over the git history

    (This should also handle normalizing them to what filter-repo expects)

    Raises subprocess.CalledProcessError if outside a repository.
    """
    log.debug("Retrieving history for: %s", path)

    lines = set(subprocess.check_output(['git', 'log',  # nosec
        '--pretty=format:', '--name-only', '--follow', '--', path
        ]).split(b'\n'))  # noqa
    results = [x for x in lines if x.strip()]

    log.debug("Found:\n\t%s",
        b'\n\t'.join(results).decode(fs_encoding, 'replace'))
    return results


def is_path_versioned(path: str) -> bool:
    """Check if the given path is under version control

    (To avoid calling `git log` on excluded files)

    NOTE: Relies on the current working directory being inside the same repo.
    Will spuriously report false otherwise.
    """
    return subprocess.call(  # nosec
        ['git', 'ls-files', '--error-unmatch', path],
        stderr=subprocess.DEVNULL) == 0


def recurse_arg(arg_path: str) -> List[str]:
    """List all files under the given path not in an un-versioned folder

    (A compromise to minimize the number of fork() calls to invoke git without
    having to reimplement path matching on the output of a full `git ls-files`)
    """
    log.debug("Recursing argument: %s", arg_path)

    results = []
    if os.path.isfile(arg_path):
        results.append(get_path_history(arg_path))
    else:
        for path, dirs, files in os.walk(arg_path):
            for dname in dirs[:]:
                if not is_path_versioned(os.path.join(path, dname)):
                    # Don't descend into un-versioned directories
                    log.debug("Skipping un-versioned directory: %s", dname)
                    dirs.remove(dname)
            for fname in files:
                results.append(os.path.join(path, fname))
    return results


def filter_repo(paths: List[str],
                repo_root: str, clone_root: str,
                gfr_cmd: List[str], rm_tags=False):
    """Create a copy of the given repo containing only the listed files"""
    log.info("Filtering paths in %s -> %s", repo_root, clone_root)
    log.debug("Paths:\n\t%s", '\n\t'.join(paths))

    # Get the list of paths to keep throughout the entire history
    # as paths relative to the root
    git_paths = []
    for arg in paths:
        for path in recurse_arg(arg):
            git_paths.extend(get_path_history(path))
    git_paths.sort()

    # Prevent bugs and regressions
    del paths
    assert not any(os.path.isabs(x) for x in git_paths), (  # nosec
        "`git log` output produced absolute paths")

    # Use --no-local so git-filter-repo without --force can protect us too
    # (And make this the first thing we do to let `git` abort the process if
    #  the target already exists.)
    subprocess.check_call(  # nosec
        ['git', 'clone', '--no-local', repo_root, clone_root])

    # Make SURE we're not operating on the original repo, since it's too
    # easy to accidentally drop a `cwd` in a subprocess call to `git`
    os.chdir(clone_root)
    assert get_git_root() == os.path.abspath(clone_root)  # nosec
    del repo_root

    if rm_tags:
        tags = [x.strip()
            for x in subprocess.check_output(  # nosec
                ['git', 'tag']).strip().split()]  # noqa
        for tag in tags:
            subprocess.check_call(['git', 'tag', '-d', tag])  # nosec

    # Can't use `with` to clean up NamedTemporaryFile because that would
    # guaranteed no compatibility with Windows.
    # (You can't reopen the file before closing it on Windows)
    pathlist_fobj = tempfile.NamedTemporaryFile(mode='wb', delete=False)
    try:
        pathlist_fobj.write(b'\n'.join(git_paths))
        pathlist_fobj.flush()
        pathlist_fobj.close()

        # Invoke git-filter-repo WITHOUT --force so that, even if we somehow
        # passed the previous safeguards and blew away our origin and tags,
        # at least such a bug won't mangle the repository's contents
        subprocess.check_call(gfr_cmd + [  # nosec
            '--paths-from-file', pathlist_fobj.name,
            '--replace-refs', 'delete-no-add'])
    finally:
        os.remove(pathlist_fobj.name)


def main():
    """The main entry point, compatible with setuptools entry points."""
    # Identify the repo root early so we can derive a default output path in
    # time to use it in --help
    try:
        repo_root = get_git_root()
    except subprocess.CalledProcessError:
        log.critical("Must be run inside a Git repository. Exiting.")
        sys.exit(1)

    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
        description=__doc__.replace('\r\n', '\n').split('\n--snip--\n')[0])
    parser.add_argument('--version', action='version',
        version="%%(prog)s v%s" % __version__)
    parser.add_argument('-v', '--verbose', action="count",
        default=2, help="Increase the verbosity. Use twice for extra effect.")
    parser.add_argument('-q', '--quiet', action="count",
        default=0, help="Decrease the verbosity. Use twice for extra effect.")
    parser.add_argument('-o', '--out-path', action="store",
        default=repo_root + b'.filtered',
        help='Output path (default: %(default)s)')
    parser.add_argument('--gfr-cmd', action="store",
        default='git filter-repo', help='Command to invoke git-filter-repo. '
        "(Default is '%(default)s'. Shell quoting is allowed)")
    parser.add_argument('--rm-tags', action="store_true",
        default=False, help="Delete the git tags from the filtered copy")
    parser.add_argument('path', action="store", nargs="+",
        help="Path to keep in the clone")
    # Reminder: %(default)s can be used in help strings.

    args = parser.parse_args()

    # Set up clean logging to stderr
    log_levels = [logging.CRITICAL, logging.ERROR, logging.WARNING,
              logging.INFO, logging.DEBUG]
    args.verbose = min(args.verbose - args.quiet, len(log_levels) - 1)
    args.verbose = max(args.verbose, 0)
    logging.basicConfig(level=log_levels[args.verbose],
                format='%(levelname)s: %(message)s')

    filter_repo(args.path, repo_root, args.out_path,
        shlex.split(args.gfr_cmd), args.rm_tags)


if __name__ == '__main__':  # pragma: nocover
    main()

# vim: set sw=4 sts=4 expandtab :