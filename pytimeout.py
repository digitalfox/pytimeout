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
TIMEOUT=10     # in seconds
RETRY=2        # number of retry to kill process
INIT_PID=1     # PID of the init process. Equal to 1 for most unices
VERSION=0.1    # Release of pytimeout

def main():
    """Just a wrapper for CLI usage to the run() function"""
    
    # Options & args stuf
    (options, argv)=parseOptions()

    if not argv:
        print "Command to launch must be supplied !"
        sys.exit(2)
    
    target=" ".join(argv)
    
    rc=run(target, options.timeout, options.retry, 
           preserveChildren=options.preserveChildren, verbose=options.verbose)
    if rc:
        sys.exit(0)
    else:
        sys.exit(1)

def run(target, timeout=TIMEOUT, retry=RETRY,
        preserveChildren=False, verbose=False):
    """Run a process but kill it after timeout
    @param target: the command to launch (str)
    @param timeout: timeout in seconds before start killing process (int)
    @param retry: Number of time we will try to kill the process with SIGTERM and SIGKILL (int)
    @param preserveChildren: Do we need to also kill process children ? Default is True (bool)
    @param verbose: Print what happened on standard output (bool)
    @return: True if everything is ok. None or False else.
    """
    
    # Some sanity checks
    if timeout<0 or retry<1:
        print "Timeout must be a positive integer and number of retry must be greater or equal than 1"
        return
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
            pids=getChildrenPid(process.pid, verbose)
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
    return True

def getChildrenPid(fatherPid, verbose=False):
    """Return a list of a process children PID
    @param pid: father pid
    @return: list of children pid (list of int)"""

    # Get all PID
    try:
        pids=[int(pid) for pid in os.listdir("/proc") if pid.isdigit()]
    except OSError:
        print "Warning, /proc does not exist or is not readable. Cannot find child process"
        return []
    
    #Build father tree
    father={}
    for pid in pids:
        try:
            for line in file(os.path.join("/proc", str(pid), "status")):
                if line.startswith("PPid"):
                    father[pid]=int(line.split(":")[1])
        except:
            # Process disapear since /proc listing above
            # Forget it silently
            pass
    
    # Look for children
    fatherNotFoundError="""Warning: I don't know who is %s's father.
This can happened if we do not have enough right to read /proc/<pids>
or if this process disapear in the interval.\n"""
    
    children=[]   
    for pid in pids:
        if not father.has_key(pid):
            if verbose:
                print fatherNotFoundError % pid 
            continue
        childPid=pid
        while pid!=INIT_PID:
            if father[pid]==fatherPid:
                children.append(childPid)
                break
            if father.has_key(pid):
                pid=father[pid]
            else:
                if verbose:
                    print fatherNotFoundError % pid
                break
    return children
        
def parseOptions():
    """Parses command argument using optparse python module
    @return: (options, argv) tuple"""
    
    usage="usage: %prog [options] <program to launch>"
    version="%%prog %s" % VERSION 
    parser=OptionParser(usage=usage, version=version)

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