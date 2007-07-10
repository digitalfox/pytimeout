#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Sébastien Renard (sebastien.renard@digitalfox.org)
# Code licensed under GNU GPL V2

"""pytimeout module.
Provide both a command line interface and an API (via the "run" function)
to allow process launching with a define time to live before being killed.
"""

# Python imports
import sys
import os
from subprocess import Popen
from time import sleep
from optparse import OptionParser

# Some constant for default values
TIMEOUT=10 # in seconds
RETRY=2  # number of retry to kill process

def main():
    """Just a wrapper for CLI usage to the run() function"""
    
    # Options & args stuf
    (options, argv)=parseOptions()

    if not argv:
        print "Command to launch must be supplied !"
        sys.exit(1)
    
    target=" ".join(argv)
    
    run(target, options.timeout, options.retry, 
        preserveChildren=options.preserveChildren, verbose=options.verbose)

def run(target, timeout=TIMEOUT, retry=RETRY,
        preserveChildren=False, verbose=False):
    """Run a process but kill it after timeout
    @param target: the command to launch (str)
    @param timeout: timeout in seconds before start killing process (int)
    @param retry: Number of time we will try to kill the process with SIGTERM and SIGKILL (int)
    @param preserveChildren: Do we need to also kill process children ? Default is True (bool)
    @param verbose: Print what happened on standard output (bool)
    """
    
    if verbose:
        print "running %s" % target

    process=Popen(target, shell=True)
    sleep(timeout)
    if process.pid is None:
        if verbose:
            print "process correctly finished"
    else:
        if preserveChildren:
            pids=[]
        else:
            pids=getChildrenPid(process.pid)
        pids.append(process.pid)
        for i in xrange(retry):
            for signal in (15, 9): # SIGTERM then SIGKILL
                for pid in pids:
                    if verbose:
                        print "kill %s with signal %s" % (pid, signal)
                    try:
                        os.kill(pid, signal)
                    except OSError, e:
                        if e.errno==1:
                            print "Not authorized to kill %s" % pid
                        elif e.errno==3:
                            # No such process - already dead
                            pass
                        else:
                            print "Error while killing %s:\n%s" % (pid, e)
                sleep(i)

def getChildrenPid(fatherPid):
    """Return a list of a process children PID
    @param pid: father pid
    @return: list of children pid (list of int)"""

    # Get all PID
    pids=[int(pid) for pid in os.listdir("/proc") if pid.isdigit()]
    
    #Build father tree
    father={}
    for pid in pids:
        for line in file(os.path.join("/proc", str(pid), "status")):
            if line.startswith("PPid"):
                father[pid]=int(line.split(":")[1])
    
    # Look for children
    children=[]   
    for pid in pids:
        childPid=pid
        while pid!=1:
            if father[pid]==fatherPid:
                children.append(childPid)
                break
            pid=father[pid]
    return children
        
def parseOptions():
    """Parses command argument using optparse python module
    @return: (options, argv) tuple"""
    
    usage = "usage: %prog [options] <program to launch>"
    parser=OptionParser(usage=usage)

    # Timeout
    parser.add_option("-t", "--timeout", dest="timeout", type="int", default=TIMEOUT,
              help="Timeout in seconds. Default is 10")

    # Retries
    parser.add_option("-r", "--retry", dest="retry", type="int", default=RETRY,
              help="Number of kill retries. Default is 2")

    # Preserve children
    parser.add_option("-p", "--preserve-children", dest="preserveChildren", action="store_true",
              help="Do not kill process children")

    # Verbose
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
              help="Tell what happened on standard output")

    return parser.parse_args()

# Main
if __name__ == "__main__":
    main()