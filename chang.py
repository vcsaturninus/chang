#!/usr/bin/python3

"""
Copyright (c) 2022, vcsaturninus -- vcsaturninus@protonmail.com
See https://github.com/vcsaturninus/chang
"""

import argparse
import os
import re
import shutil         # rm dir tree
import subprocess
import sys
import time
from typing import List, Pattern

WORKDIR="._repos/"
PWD=os.getcwd()
VERBOSE=True


class Repo:
    """Encapsulate repository details and operations.

    Used to abstract and encapsulate fundamental repository details
    into a repo object, for user-friendliness. Details may include
    the name and url of the repo.
    """
    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self.url  = url
        self.path: str = None
        self.commits: List[str] = []

    def __str__(self) -> str :
        return self.name

    def get_name(self) -> str:
        """Get repository name"""
        return self.name

    def get_url(self) -> str:
        """Get repository URL"""
        return self.url

    def get_commits(self) -> List[str]:
        """Get list of commits extracted for this repo"""
        return self.commits

    def clone_or_fetch(self, path: str) -> None:
        """Clone the repository found at the specified URL into PATH.

        The name of repository is appended to PATH. The resulting path
        is created if it does not exist. If the resulting path DOES exist
        it MUST be a git repo and this function will attempt to run
        `git fetch -a` inside it. The user must have access rights to the
        specified repo such that it can be cloned or fetched from.
        """
        git_cmd = None
        path = os.path.abspath(path + self.name)

        # if path already exists but it is not a dir, remove it;
        # if it exists and it is a dir, fetch;
        # else if it does not exist, create the path and clone.
        if os.path.exists(path) and not os.path.isdir(path):
            os.remove(path)

        if os.path.exists(path):
            git_cmd = f"git -C {path} fetch -a"
        else:
            os.makedirs(path)
            git_cmd = f"git clone {self.url} {path}"

        try:
            subprocess.run(git_cmd,
                           text=True,
                           timeout=100,
                           check=True,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = e.stdout.strip()
            print(f' !! Command "{git_cmd}" failed with error code {e.returncode}: \n"{colorize(output, "red")}"')
            sys.exit(11)
        else:
            self.path = path

    def scrape_commits(self,
                       start: str = None,
                       end:   str = None,
                       match_list: List[Pattern] = None,
                       excl_list:  List[Pattern] = None
                       ) -> None:
        """Extract matching commits from repository.

        Get a list of one-line git commit messages that are between [start, end],
        where start and end are either git commits or git tags.

        If match_list is specified, the commits not matching the pattern are filtered out.
        If exclude is specified, the commits matching the exclude pattern are filtered out.
        """
        # reset any previous results from previous invocations
        self.commits = []

        cmd = "git log --oneline"
        check_tag_semantics(start, end)

        if start and end:
            cmd = f"{cmd} {start}..{end}"

        log(VERBOSE, f' ::=> extracting commit set from {self.name} with command "{cmd}"')
        ret = None
        os.chdir(self.path)

        try:
            ret = subprocess.run(cmd,
                                  timeout=100,               # 100 seconds timeout
                                  check=True,                # throw error if cmd returns error code
                                  shell=True,
                                  text=True,
                                  stdout=subprocess.PIPE,    # save stdout
                                  stderr=subprocess.STDOUT   # 2>&1
                                  )
        except subprocess.CalledProcessError as e:
            output = e.stdout.strip()
            print(f' !! Command "{cmd}" failed with error code {e.returncode}: \n"{colorize(output, "red")}"')
        else:
            output = ret.stdout.strip()
            # remove starting commit hash (first field)
            for line in output.split('\n'):
                line = line.split()
                line = ' '.join(line[1:])
                # only save non-empty lines that pass all filters
                if line != '' and matches(line, match_list, excl_list):
                    self.commits.append(line)
        finally:
            os.chdir(PWD)


class TagError(Exception):
    """Error for incorrect tag semantics

    Start and end tags/commits must be specified as a pair: they must
    either both be passed or neither should be passed. Passing only one
    is an error and this exception will be raised.
    """
    def __init__(self) -> None:
        errmsg = "Invalid semantics: must pass either both or neither of start and end tags."
        super().__init__(errmsg)


def check_tag_semantics(start_tag: str=None, end_tag: str=None):
    """Raise appropriate exception if only one of start_tag and end_tag is not None

    See TagError.
    """
    if start_tag and not end_tag or end_tag and not start_tag:
        raise TagError()


def dump_changelog(repos: List[Repo], outfile: str = None, start_tag: str = None, end_tag: str = None) -> None:
    """Print commit set to stdout or outfile.

    Write the matching commit set either to stdout or otherwise
    if outfile is not None, to OUTFILE. The specified file is
    truncated and created if it does not exist.
    """
    check_tag_semantics(start_tag, end_tag)

    if outfile:
        with open(outfile, "wt") as f:
            # timestamp only needed when writing to file
            timestamp = time.strftime("%b %d %Y")

            if start_tag or end_tag:
                print(f"~~ Changelog generated {timestamp} [{start_tag}, {end_tag}] ~~\n", file=f)
            else:
                print(f"~~ Changelog generated {timestamp} ~~\n", file=f)

            for repo_ in repos:
                commits = repo_.get_commits()
                for i in commits:
                    # colors are meaningless when writing to file
                    print(f"[{repo_}] {i}", file=f)
    else:
        for repo_ in repos:
            commits = repo_.get_commits()
            for i in commits:
                print(f"[{colorize(repo_, 'green')}] {i}")


def matches(s: str, match_list: List[Pattern] = None, excl_list: List[Pattern] = None) -> bool:
    """Match s against the specified list(s) of Regex patterns.

    True if s matches every single pattern in match_list and does
    NOT match ANY pattern in excl_list. Otherwise False.

    Both match_list and excl_list are optional. If both are None,
    calling this function always returns True.
    """
    if match_list:
        for pattern in match_list:
            if not pattern.search(s):
                return False

    if excl_list:
        for pattern in excl_list:
            if pattern.search(s):
                return False

    # passsed all filters
    return True


def colorize(s: str, color: str = None) -> str:
    """Decorate with ASCII colors (terminal color codes).

    If color is not specified (default), s is returned as is.
    """
    colors = {
        'black': '\u001b[30m',
        'red': '\u001b[31m',
        'green': '\u001b[32m',
        'yellow': '\u001b[33m',
        'blue': '\u001b[34m',
        'magenta': '\u001b[35m',
        'cyan': '\u001b[36m',
        'white': '\u001b[37m'
        }

    reset = '\u001b[0m'

    color = colors[color]
    if not color:
        return s                      # nothing, undecorated

    return f"{color}{s}{reset}"       # decorate, colorize


def log(decider: bool, msg: str) -> None:
    """Only print msg to stdout if decider == True."""
    if decider:
        print(msg)


def rmdir(path: str, recreate: bool = True) -> None:
    """Remove directory tree recursively.

    PATH must exist and be either a relative path to the current working
    directory or an absolute path. The directory removed is then recreated
    if recreate == True (default) in which case this is equivalent to removing
    only the contents of the directory.
    """
    path = os.path.abspath(path)

    try:
        shutil.rmtree(path)
    except FileNotFoundError:        # 'rm -rf' behavior
        pass

    if recreate:
        os.mkdir(path)


def read_repos_from_file(srcf: str, repoq: List[Repo], restrict: List[str] = None) -> None:
    """Populate repoq with a list of Repo instances based on contents read from file srcf.

    srcf must be a file listing git repository URLs, one per line. Each line is parsed and
    a Repo instance is created based on that and appended to the queue repoq.
    """
    with open(srcf, "rt") as f:
        for line in f.readlines():
            repo_url = line.strip()
            # skip empty lines
            if repo_url == '':
                continue

            # break down into basic components of interest: name and url
            repo_name = repo_url.split('/')[-1]        # name of the repo is the last component
            repo_name = repo_name.replace(".git", "")  # strip off .git extension substring if present

            # if list of repo names to filter for is specified skip non-matching repos
            if restrict and repo_name not in restrict:
                continue

            repoq.append(Repo(repo_name, repo_url))



# =============================================================== #
#                      MAIN                                       #
# --------------------------------------------------------------- #

parser = argparse.ArgumentParser(description='Git Changelog Generator')
parser.add_argument('-s',
                     '--start-tag',
                     metavar='TAG',
                     dest='start_tag',
                     help='Tag to start searching from (inclusive)'
                     )

parser.add_argument('-e',
                     '--end-tag',
                     metavar='TAG',
                     dest='end_tag',
                     help='Do not look at commits past this tag (inclusive)'
                     )

parser.add_argument('-i',
                     '--input',
                     required=True,
                     metavar='FILE',
                     dest='repos',
                     help='read list of repos from FILE. The file should contain repository URLs, one per line.'
                     )

parser.add_argument('-o',
                     '--output',
                     metavar='FILE',
                     dest='outfile',
                     help='Write output to FILE instead of stdout. Verbose/Diagnostic prints are NOT included'
                     )

parser.add_argument('--match',
                     nargs='*',                 # support any number of args
                     metavar='PATTERN',
                     dest='match',
                     help='Filter out commits that do NOT match PATTERN'
                     )

parser.add_argument('--exclude',
                     nargs='*',                 # support any number of args
                     metavar='PATTERN',
                     dest='exclude',
                     help='Filter out commits that match PATTERN'
                     )

parser.add_argument('-c',
                     '--clean',
                     action='store_true',
                     dest='clean',
                     help='Start clean/fresh: remove previously cloned repositories.'
                     )

parser.add_argument('-q',
                    '--quiet',
                     action='store_true',
                     dest='quiet',
                     help='Do not print verbose/diagnostic messages'
                     )

parser.add_argument('-r',
                     '--repo',
                     nargs='*',                 # support any number of args
                     metavar="REPO",
                     dest='restrict',
                     help='Only look at the specified repos, ignoring the other repos supplied via the input file'
                     )


args = parser.parse_args()

repo_objs: List[Repo] = []       # repository objects; repos to clone and extract changelog from
read_repos_from_file(args.repos, repo_objs, args.restrict)

# REGEX lists; the cli allows specification of arbitrary number of filters
pat  = [re.compile(m, re.IGNORECASE) for m in args.match ] if args.match else None
excl = [re.compile(m, re.IGNORECASE) for m in args.exclude] if args.exclude else None

# remove past clones IFF starting clean
if args.clean:
    rmdir(WORKDIR)

# check if silent mode enabled (verbose by default)
if args.quiet:
    VERBOSE=False

for repo in repo_objs:
    log(VERBOSE, f"\n => Getting latest {repo} from {repo.get_url()}")
    repo.clone_or_fetch(WORKDIR)
    repo.scrape_commits(start=args.start_tag, end=args.end_tag, match_list=pat, excl_list=excl)

dump_changelog(repo_objs, args.outfile, args.start_tag, args.end_tag)
