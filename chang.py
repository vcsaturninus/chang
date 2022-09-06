#!/usr/bin/python3

"""
Copyright (c) 2022, vcsaturninus -- vcsaturninus@protonmail.com
See https://github.com/vcsaturninus/chang
"""

import argparse
import os
import shutil         # rm dir tree
import sys
import subprocess
import re

WORKDIR="._repos/"
PWD=os.getcwd()
QUIET=False

def colorize(s, color=None):
    """
    Decorate s with ASCII colors (terminal color codes).
    If color is not specified (default), s is returned as is.
    """
    colors = {
        'black': u'\u001b[30m',
        'red': u'\u001b[31m',
        'green': u'\u001b[32m',
        'yellow': u'\u001b[33m',
        'blue': u'\u001b[34m',
        'magenta': u'\u001b[35m',
        'cyan': u'\u001b[36m',
        'white': u'\u001b[37m'
        }
    reset = u'\u001b[0m'

    color = colors[color]
    if not color:
        return s                          # nothing, undecorated
    else:
        return f"{color}{s}{reset}"       # decorate, colorize


def log(decider, msg):
    """
    Only print msg to stdout if decider == True
    """
    if decider:
        print(msg)


def rmdir(path, recreate=True):
    """
    Remove PATH recursively. PATH must exist and be either a relative path
    to the current working directory or an absolute path.
    The directory removed is then recreated if recreate=True (default) in
    which case this is equivalent to removing only the contents of the
    directory.
    """
    path = os.path.abspath(path)

    try:
        shutil.rmtree(path)
    except FileNotFoundError:        # 'rm -rf' behavior
        pass

    if recreate:
        os.mkdir(path)


def matches(s, match_list=None, excl_list=None):
    """
    True if s matches every single pattern in match_list
    and does NOT match ANY pattern in excl_list. Otherwise
    False.

    Both match_list and excl_list are optional. If both are None,
    calling this function always returns True.
    """
    if match_list:
        for pat in match_list:
            if not pat.search(s):
                return False

    if excl_list:
        for pat in excl_list:
            if pat.search(s):
                return False

    # passsed all filters
    return True


class Repo:
    """
    Used to abstract fundamental repository details into
    a repo object, for user-friendliness. Details may include
    the name and url of the repo.
    """
    def __init__(self, name, url):
        self.name    = name
        self.url     = url
        self.path    = None
        self.commits = []

    def __str__(self):
        return self.name

    def get_name(self):
        return self.name

    def get_url(self):
        return self.url

    def get_commits(self):
        return self.commits

    def clone_or_fetch(self, path):
        """
        Clone the repository found at the specified url into the directory
        specified by PATH. PATH is created if it does not exist. If PATH
        does exist, it MUST be a git repo and this function will attempt
        to run `git fetch -a` inside it.
        The user must have access rights to the specified repo such that
        it can be cloned or fetched from.
        """
        git_cmd = None
        if os.path.exists(path):
            if not os.path.isdir(path):
                os.remove(path)
            else:       # directory exists
                git_cmd = f"git -C {path} fetch -a"
        else:
            os.mkdir(path)
            git_cmd = f"git clone {self.url} {path}"

        path = os.path.abspath(path)
        ret = None

        try:
            ret = subprocess.run(git_cmd,
                                 text=True,
                                 timeout=100,
                                 check=True,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            output = e.stdout.strip()
            print(f'Command "{git_cmd}" failed with error code {e.returncode}: \n"{output}"')
            exit(11)
        else:
            self.path = path


    def scrape_commits(self, start=None, end=None, match_list=None, excl_list=None):
        """
        Get a list of one-line git commit messages that are between [start, end],
        where start and end are either git commits or git tags.

        If pattern is specified, the commits not matching the pattern are filtered out.
        If exclude is specified, the commits matching the exclude pattern are
        filtered out.
        """
        cmd = f"git log --oneline"
        if start and not end or end and not start:
            raise(Exception("Start and end commits must both be either specified or unspecified"))
        elif start and end:
            cmd = f"{cmd} {start}..{end}"

        ret = None

        os.chdir(self.path)
        try:
            ret = subprocess.run(cmd,
                                  timeout=100,                      # 100 seconds timeout
                                  check=True,                       # throw error if cmd returns error code
                                  shell=True,
                                  text=True,
                                  stdout=subprocess.PIPE,           # save stdout
                                  stderr=subprocess.STDOUT          # 2>&1
                                  )
        except subprocess.CalledProcessError as e:
            output = e.stdout.strip()
            print(f'Command "{cmd}" failed with error code {e.returncode}: \n"{output}"')
            exit(11)
        else:
            output = ret.stdout.strip()
            # remove starting commit hash (first field)
            for line in output.split('\n'):
                line = line.split()
                line = ' '.join(line[1:])
                if matches(line, match_list, excl_list):
                    self.commits.append(line)

        finally:
            os.chdir(PWD)



parser = argparse.ArgumentParser(description='Changelog Scraper based on tags')
parser.add_argument('-s',
                     '--start-tag',
                     nargs=1,
                     metavar='TAG',
                     dest='start_tag',
                     help='Tag to start searching from (inclusive)'
                     )

parser.add_argument('-e',
                     '--end-tag',
                     nargs=1,
                     metavar='TAG',
                     dest='end_tag',
                     help='Do not look at commits past this tag (inclusive)'
                     )

parser.add_argument('-f',
                     '--repos-list',
                     required=True,
                     metavar='FILE',
                     dest='repos',
                     help='read list of repos from FILE. The file should contain repository URLs, one per line.'
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
                     nargs='*',                 # support any number of params
                     metavar="REPO",
                     dest='repo',
                     help='Only look at the specified repos, ignoring the other repos supplied via the input file'
                     )


args = parser.parse_args()

repos = []       # repository objects; repos to clone and extract changelog from


# build up repo object list
with open(args.repos, "r") as f:
    for line in f.readlines():
        # break down into basic components of interest: name and url
        url = line.strip()
        name = url.split('/')[-1]           # name of the repo is the last component
        name = name.replace(".git", "")     # strip off .git extension substring if present

        # skip if single repo (-r) is specified and != current
        if args.repo and name not in args.repo:
            continue

        repos.append(Repo(name, url))

print(args.match, args.exclude)

# remove past clones IFF starting clean
if args.clean:
    rmdir(WORKDIR)

# check if silent mode enabled (verbse by default)
if args.quiet:
    QUIET=True

# REGEX lists; the cli allows specification of arbitrary number of filters
pat  = [re.compile(m) for m in args.match ] if args.match else None
excl = [re.compile(m) for m in args.exclude] if args.exclude else None

for repo in repos:
    log(not QUIET, f" => Getting latest {repo} from {repo.get_url()}")
    repo.clone_or_fetch(WORKDIR + repo.get_name())
    repo.scrape_commits(start=args.start_tag, end=args.end_tag, match_list=pat, excl_list=excl)

for repo in repos:
    l = repo.get_commits()
    for i in l:
        print(f"[{colorize(repo, 'green')}] {i}")
