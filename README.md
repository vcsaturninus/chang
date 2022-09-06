# chang
Git Changelog generator

`Chang`  - short for `CHANgelog Generator` can be used to extract commits from
across a list of repositories specified via an input file.

The script is designed to be flexible as regards the collection of commits
extracted:
 * a `python3` regular expression pattern can specified via the `--match`
   option; only commits _matching_ this pattern will be included
 * another such pattern can be specified via the `--exclude` option; commits
   matching this will be _filtered out_.
 * a range (`[start, end]`) of commits or tags can be specified to better pinpoint 
   in time the commits of interest. Since commit hashes are specific to each
   repository, the range end points will normally be _tags_ common to all
   repositories, rather than commits.

The script does what it can to help, but ultimately it all comes down to how
well formatted the commit messages are. It's recommended that the `conventional commits`
standard or some other such standard for commit messages be followed consistently so that 
commit message lines appear in an expected format that simplifies pattern matching (and 
changelog generation).


## Todo:
 * small cleanup/refactoring
 * flesh out readme with examples/overview notes
