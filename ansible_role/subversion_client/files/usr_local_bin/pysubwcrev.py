#!/usr/bin/env python3
#
# This file is part of pysubwcrev.
#
# pysubwcrev is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pysubwcrev is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pysubwcrev.  If not, see <http://www.gnu.org/licenses/>.

from io import FileIO
from time import strftime, gmtime, localtime
import os, pysvn, re, sys
import tempfile
import shutil

def gather(workingCopyDir, opts):

    if not os.path.exists(workingCopyDir):
        sys.exit("Working copy directory does not exist");

    isSingleFile = os.path.isfile(workingCopyDir)

    client = pysvn.Client()
    svnEntry  = client.info(workingCopyDir)

    maxdate = 0
    maxrev = 0
    minrev = 0
    hasMods = False
    inSvn = True
    needslock = False
    filerev = -1
    islocked = False
    lockeddata = 0
    lockowner = ""
    lockcomment = ""

    # ignore externals if e isn't a given option
    ignoreExt = 'e' not in opts

    try:
        for stat in client.status(workingCopyDir, ignore_externals=ignoreExt):
            # skip externals if desired
            if stat.text_status == pysvn.wc_status_kind.external and ignoreExt:
                continue;
    
            if stat.entry:
                # skip directories if not specified
                if stat.entry.kind == pysvn.node_kind.dir and 'f' not in opts:
                    continue;
                if stat.entry.revision.number > maxrev:
                    maxrev = stat.entry.revision.number
                if stat.entry.revision.number < minrev or 0 == minrev:
                    minrev = stat.entry.revision.number
                if stat.entry.commit_time > maxdate:
                    maxdate = stat.entry.commit_time
                if stat.text_status == pysvn.wc_status_kind.modified or \
                    stat.prop_status == pysvn.wc_status_kind.modified:
                    hasMods = True

                if isSingleFile:
                    prop_list = client.proplist(stat.entry.url)
                    if len(prop_list) > 0 and len(prop_list[0]) > 1 and "svn:needs-lock" in prop_list[0][1]:
                        needslock = True

                    #TODO: I am not very sure about the different between entry revision and file revisions
                    #This code get same result with SubWCRev.exe in my test
                    #No api to get 'current' file revision, just the 1st one lower then current entry revision
                    logs = client.log(stat.entry.url,revision_start=pysvn.Revision( pysvn.opt_revision_kind.number, minrev),limit=1)
                    if len(logs) > 0:
                        filerev = logs[0].revision.number

                    entry_list = client.info2(stat.entry.url)
                    if len(entry_list) > 0 \
                            and len(entry_list[0]) > 1 \
                            and "lock" in entry_list[0][1] \
                            and entry_list[0][1].lock != None:
                        islocked = True
                        lockeddata = entry_list[0][1].lock.creation_date
                        lockowner = entry_list[0][1].lock.owner
                        lockcomment = entry_list[0][1].lock.comment

    except pysvn.ClientError:
        inSvn = False

    # assume mixed, w/range, fix if needed
    wcrange = "%s:%s" % (minrev, maxrev)
    isMixed = True
    if minrev == maxrev:
        wcrange = "%s" % (maxrev)
        isMixed = False

    results = {
        '_wcmaxdate': maxdate,
        'wcrange' : wcrange,
        'wcmixed' : isMixed,
        'wcmods'  : hasMods,
        'wcrev'   : filerev if filerev>0 else maxrev,
        'wcurl'   : "" if svnEntry == None else svnEntry.url,
        'wcdate'  : strftime("%Y/%m/%d %H:%M:%S", localtime(maxdate)),
        'wcnow'   : strftime("%Y/%m/%d %H:%M:%S", localtime()),
        'wcdateutc'     : strftime("%Y/%m/%d %H:%M:%S", gmtime(maxdate)),
        'wcnowutc'      : strftime("%Y/%m/%d %H:%M:%S", gmtime()),
        'wcinsvn'       : inSvn,
        'wcneedslock'   : needslock,
        '_wclockdate'   : lockeddata,
        'wcislocked'    : islocked,
        'wclockdate'    : strftime("%Y/%m/%d %H:%M:%S", localtime(lockeddata)),
        'wclockdateutc' : strftime("%Y/%m/%d %H:%M:%S", gmtime(lockeddata)),
        'wclockowner'   : lockowner,
        'wclockcomment' : lockcomment,
    }

    return results

def boolean_process(inline,replacekey,boolean_value):
    match = re.search(r'\$'+replacekey+r'\?(.*):(.*)\$', inline)
    if match:
        idx = 1
        if not boolean_value:
            idx = 2
        return re.sub(r'\$'+replacekey+r'.*\$', match.group(idx), inline)
    else:
        return inline

def strftime_process(inline,replacekey,date_value):
    match = re.search(r'\$'+replacekey+r'=(.*)\$', inline)
    if match:        
        datestr = strftime(match.group(1), date_value)
        return re.sub(r'\$'+replacekey+r'=.*\$', datestr, inline)
    else:
        return inline

def FlushDestFile(tempFile: FileIO, outFile: str) -> bool:
    same = False
    with open(outFile, 'a+') as fout:
        tempFile.seek(0)
        fout.seek(0)
        same = tempFile.read() == fout.read()

    if not same:
        tempFile.seek(0)
        with open(outFile, 'w+') as fout:
            shutil.copyfileobj(tempFile, fout)

    return same

def process(inFile: str, outFile: str, info, opts):
    # if wanted, exit if the out file exists
    if 'd' in opts and os.path.exists(outFile):
        sys.exit(9)
        
    with open(inFile, 'r') as fin:
        with tempfile.SpooledTemporaryFile(mode='w+') as tempFile:
            for line in fin:
                tmp = re.sub(r'\$WCDATE\$', str(info['wcdate']), line)
                tmp = re.sub(r'\$WCNOW\$', str(info['wcnow']), tmp)
                tmp = re.sub(r'\$WCDATEUTC\$', str(info['wcdateutc']), tmp)
                tmp = re.sub(r'\$WCNOWUTC\$', str(info['wcnowutc']), tmp)
                tmp = re.sub(r'\$WCRANGE\$', str(info['wcrange']), tmp)
                tmp = re.sub(r'\$WCREV\$', str(info['wcrev']), tmp)
                tmp = re.sub(r'\$WCURL\$', str(info['wcurl']), tmp)
                tmp = re.sub(r'\$WCLOCKDATE\$', str(info['wclockdate']), tmp)
                tmp = re.sub(r'\$WCLOCKDATEUTC\$', str(info['wclockdateutc']), tmp)
                tmp = re.sub(r'\$WCLOCKOWNER\$', str(info['wclockowner']), tmp)
                tmp = re.sub(r'\$WCLOCKCOMMENT\$', str(info['wclockcomment']), tmp)

                tmp = boolean_process(tmp,"WCMODS",info['wcmods'])
                tmp = boolean_process(tmp,"WCMIXED",info['wcmixed'])
                tmp = boolean_process(tmp,"WCINSVN",info['wcinsvn'])
                tmp = boolean_process(tmp,"WCNEEDSLOCK",info['wcneedslock'])
                tmp = boolean_process(tmp,"WCISLOCKED",info['wcislocked'])

                tmp = strftime_process(tmp,"WCDATE",localtime(info['_wcmaxdate']))
                tmp = strftime_process(tmp,"WCDATEUTC",gmtime(info['_wcmaxdate']))

                tmp = strftime_process(tmp,"WCLOCKDATE",localtime(info['_wclockdate']))
                tmp = strftime_process(tmp,"WCLOCKDATEUTC",gmtime(info['_wclockdate']))

                tempFile.write(tmp)

            FlushDestFile(tempFile, outFile)

def doArgs(argstring):
    return [c for c in ['n', 'm', 'd', 'f', 'e'] if argstring.find(c) > 0]

if __name__ == "__main__":
    usage = """usage: pysubwcrev workingCopyPath [SrcVersionFile DestVersionFile] [-nmdfe]
"""

    if len(sys.argv) not in (2, 3, 4, 5):
        sys.exit(usage)

    workingCopyDir = os.path.abspath(sys.argv[1].strip())

    #pysvn issue: http://tigris-scm.10930.n7.nabble.com/Bug-with-status-on-a-file-if-path-uses-as-separator-td78156.html
    workingCopyDir = workingCopyDir.replace("\\","/")
    
    shouldProcess = False
    destFile = ''
    srcFile = ''
    opts = []

    if len(sys.argv) == 3: # just path and args
        opts = doArgs(sys.argv[2])
    elif len(sys.argv) == 4: # just files
        srcFile = os.path.abspath(sys.argv[2].strip())
        if not os.path.exists(srcFile):
            sys.exit('Source file not found')
        destFile = os.path.abspath(sys.argv[3].strip())
        shouldProcess = True
    elif len(sys.argv) == 5: # files and args
        srcFile = os.path.abspath(sys.argv[2].strip())
        if not os.path.exists(srcFile):
            sys.exit('Source file not found')
        destFile = os.path.abspath(sys.argv[3].strip())
        shouldProcess = True
        opts = doArgs(sys.argv[4])

    #print opts

    repoInfo = gather(workingCopyDir, opts)
    #print repoInfo

    if 'n' in opts and repoInfo['wcmods']:
        sys.exit(7)
    elif 'm' in opts and repoInfo['wcmixed']:
        sys.exit(8)

    if shouldProcess:
        process(srcFile, destFile, repoInfo, opts)
