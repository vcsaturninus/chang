# chang
Git Changelog generator

`Chang`  - short for `CHANgelog Generator` can be used to extract commits from
across a list of repositories specified via an input file.

The script is designed to be flexible as regards the collection of commits
extracted:
 * an arbitrary number of `python3` regular expression patterns can specified
   as arguments to the `--match` option; only commits _matching_ ALL of the specified
   patterns will be included.
 * another such set of patterns can be specified as arguments to the `--exclude`
   option; only commits matching NONE of the specified patterns will be
   included.
 * a range (`[start, end]`) of commits or tags can be specified to better pinpoint
   the commits of interest. Since commit hashes are specific to each
   repository, the range endpoints will normally be _tags_ common to all
   repositories, rather than commits.

The script does what it can to help, but ultimately it all comes down to how
well formatted the commit messages are. It's recommended that the `conventional commits`
standard or some other such standard for commit messages be followed consistently so that
commit message lines appear in an expected format that simplifies pattern matching (and
changelog generation).

## Example

The output in the examples below is truncated for brevity.

Given an input file such as the following (`repos.txt`):
```
https://github.com/vcsaturninus/nc.git
https://github.com/vcsaturninus/mover.git
https://github.com/vcsaturninus/mockit.git
https://github.com/vcsaturninus/cinic.git
https://github.com/vcsaturninus/bitr.git
```
`chang.py` can be called as follows.

 * clone all repositories and extract all commits from the default branch:
```sh
└─$ ./chang.py -i repos.txt
 => Getting latest nc from https://github.com/vcsaturninus/nc.git
 => extracting commit set from nc with command "git log --oneline"
 => Getting latest mover from https://github.com/vcsaturninus/mover.git
 => extracting commit set from mover with command "git log --oneline"
 => Getting latest mockit from https://github.com/vcsaturninus/mockit.git
 => extracting commit set from mockit with command "git log --oneline"
 => Getting latest cinic from https://github.com/vcsaturninus/cinic.git
 => extracting commit set from cinic with command "git log --oneline"
 => Getting latest bitr from https://github.com/vcsaturninus/bitr.git
 => extracting commit set from bitr with command "git log --oneline"
[nc] chore!: repace unfeasible --noauth option with --noverify
[nc] docs: update README md - remove outdated info and add TLS examples
[nc] chore: perform large cleanup and write up README
[nc] chore: only clean when explicitly instructed
[nc] Initial commit
[mover] chore: change version to semver string and add license title
[mover] chore: clean up by removing unnecessary code etc
[mover] docs: add Lua syntax coloring to markdown readme
```
 * remove past clones (start clean), run quietly, and extract all commits
   from the default branch:
```
└─$ ./chang.py -i repos.txt -q -c
[nc] chore!: repace unfeasible --noauth option with --noverify
[nc] docs: update README md - remove outdated info and add TLS examples
[nc] chore: perform large cleanup and write up README
[nc] chore: only clean when explicitly instructed
[mover] docs: slightly expand the README and fix grammar
[mover] chore: bring code and tests into alignment with latest docs
[mover] docs: add README markdown writeup
```
 * do not start clean - use past clones and simply fetch; run quietly and
   only extract commits matching matching the 'feat' or 'fix' `conventional
   commits` tags:
```
└─$ ./chang.py -i repos.txt -q --match 'feat!?:|fix!?:'
[nc] feat: add unix domain socket support
[mockit] feat: add new luamockit inqueue function
[mockit] feat!: commit slight redesign of mockit API and update tests accordingly
[cinic] feat!: implement support for multi-line lists and multi-word values
[cinic] fix: allow changing the section namespace delimiter char dynamically
[bitr] feat!: change new signature to take specification param for all 1s/all 0s initialization
[bitr] feat: implement lua interface to C bitr
```
 * exclude all commits matching 'chore', 'test', or 'init' and only extract commits matching
   either 'docs' or 'feat'. Only look at the `mockit` and `bitr` repositories
   (ignore the rest specified in the input file). Note `--exclude chore test
   init` could alternatively be specified via a single pattern: --exclude
   'chore|test|init'.
```
./chang.py -i repos.txt -q --exclude 'chore' 'test' 'init' --match 'docs|feat' -r mockit bitr
[mockit] docs: fix comment in README lua code snippet
[mockit] feat: add new luamockit inqueue function
[mockit] docs: flesh out README and luamockit.md
[mockit] docs: fix hyperlinks in docs
[mockit] docs: add C code examples and diagrams
[mockit] feat: update Makefile with new targets
[mockit] docs: add high-level module description and usage example to README
[bitr] docs: fix typos in README
[bitr] docs: update README md
[bitr] docs: update README with usage overview of C and Lua libs
[bitr] feat: implement lua interface to C bitr
```

 * extract commits from across all repos specified in the input file but only
   between the `rc.1` and `beta.3` tags (both inclusive). Only extract commits
   matching the `feat` tag/substring and write the extracted commits to
   `changelog.txt`:
```
./chang.py -i repos.txt --match 'feat' -s 'rc.1' -e 'beta.3' -o changelog.txt

└─$ cat changelog.txt
~~ Changelog generated Tue Sep 6 2022 [rc.1, beta.3] ~~

[nc] feat: add unix domain socket support
[mockit] feat: add new luamockit inqueue function
[mockit] feat!: commit slight redesign of mockit API and update tests accordingly
[mockit] feat: add standalone C tests for mockit
[mockit] feat: update Makefile with new targets
[cinic] feat: recompile object files on header change
[cinic] feat: make debug prints togglable via make call
[cinic] feat!: implement support for multi-line lists and multi-word values
```
