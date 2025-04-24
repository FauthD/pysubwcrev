# pysvnwcrev

[TortoiseSVN's](http://tortoisesvn.net) [SubWCRev](http://tortoisesvn.net/docs/release/TortoiseSVN_en/tsvn-subwcrev.html) app is windows-only.
For those developing cross-platform apps, it's nice to have a command-line compatible alternative to swap into the build process.
Only dependencies are Python and pysvn.

## Rational
There is a Linux version of SubWcRev called svnwcrev, that still works in many cases. Though lately I had issues with binary files
(UTF-8 error), so I looked for an update, just to find out that tigris is dead since 2020.
Since I still had the   sources, I published them on git for reference https://github.com/FauthD/svnwcrev.

While looking for a solution to my UTF-8 issues, I found https://github.com/nickveys/pysubwcrev , but that was written in Python2.
For luck only 3 lines needed a change, so I forked and provide that here.

## Build on Ubuntu (24.04)

- sudo apt install python3-svn subversion
- sudo cp src/pysubwcrev.py /usr/local/bin

### optional create symlinks for the old names

- sudo ln -s /usr/local/bin/pysubwcrev.py /usr/local/bin/subwcrev
- sudo ln -s /usr/local/bin/pysubwcrev.py /usr/local/bin/SubWcRev

## Build general
You can also use pip to install the required library.

- pip3 install pysvn

## Ansible role to install pysvnwcrev
Also uninstalls the good old C-Based svnwcrev and links.
Various symlinks are created with different flavours of names.

# Hints
- Avoid using the keywords TimeNowUTC and TimeNow, they trigger the regeneration of the destination file and therefore can trigger an undesired rebuild of make targets.
- Name the template and destination files the same in all projects. E.g.: svn_rev.tmpl and svn_rev.EXT (EXT depends on your project).
- Use make or cmake rules that regenerate svn_rev.EXT on every build.
- Use a marker that tells you whether the build is based on modified (uncommitted) sources).
You can append this to your version number to do that: "\$WCMODS?M:\$". It adds an 'M' for uncommited sources.
- Or use an "#if \$WCMODS?1:0\$" construct if your language allows it (like C/C++ preprocessor) and fire an error for uncommiteted sources (in release builds). Though sometimes this can be inflexible.
- Example for a very simple template file:
  
	`// Revision in SVN (created by SubWCRev)`

	`SVN_RevisionStr="R\$WCREV\$\$WCMODS?M:\$";`
