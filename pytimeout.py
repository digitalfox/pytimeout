#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Sébastien Renard (sebastien.renard@digitalfox.org)
# Code licensed under GNU GPL V2

# Python imports
import sys
import os
from subprocess import Popen
from time import sleep
from optparse import OptionParser

def main():

    # Options & args stuf
    (options, argv)=parseOptions()

    target=" ".join(argv)
    print "running %s" % target

    
    #TODO: define this in a separate function that could be easiliy called from
    # another python program
    process=Popen(target, shell=True)
    sleep(options.timeout)
    if process.pid is None:
        print "process correctly finished"
    else:
        pids=getChildrenPid(process.pid)
        pids.append(process.pid)
        for i in xrange(options.retry):
            for signal in (15, 9):
                for pid in pids:
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
    @arg pid: father pid"""
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
    """Parses command argument using optparse python module"""
    parser=OptionParser()

    # Timeout
    parser.add_option("-t", "--timeout", dest="timeout", type="int", default=10,
              help="Timeout in seconds. Default is 10")

    # Retries
    parser.add_option("-r", "--retry", dest="retry", type="int", default=2,
              help="Number of kill retries. Default is 2")

    # Preserve children
    parser.add_option("-p", "--preserve-children", dest="preserveChildren", action="store_true",
              help="Do not kill process children")

    return parser.parse_args()

# Main
if __name__ == "__main__":
    main()