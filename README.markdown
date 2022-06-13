[TortoiseSVN's](http://tortoisesvn.net) [SubWCRev](http://tortoisesvn.net/docs/release/TortoiseSVN_en/tsvn-subwcrev.html) app is windows-only. 
For those developing cross-platform apps, it's nice to have a command-line compatible alternative to swap into the build process. 
Only dependencies are Python and pysvn.

## Rational
There is a Linux version of SubWcRev called svnwcrev, that still works in many cases. Though lately I had issues with binary files
(UTF-8 error), so I looked for an update, just to find out that tigris is dead since 2020.
Since I still had the   sources, I published them on git for reference https://github.com/FauthD/svnwcrev.

While looking for a solution to my UTF-8 issues, I found https://github.com/nickveys/pysubwcrev , but that was written in Python2.
For luck only 3 lines needed a change, so I forked and provide that here.

## Build on Ubuntu (20.04)

- sudo apt install python3-svn
- sudo cp src/pysubwcrev.py /usr/local/bin
### optional create symlinks for the old names

- sudo ln -s /usr/local/bin/pysubwcrev.py /usr/local/bin/subwcrev
- sudo ln -s /usr/local/bin/pysubwcrev.py /usr/local/bin/SubWcRev
## Build general
You can also use pip to install the required library.

- pip3 install pysvn