#!/bin/sh
~/src/svn2cl-0.7/svn2cl.sh --group-by-day file:///home/fox/prog/depot/trunk/pytimeout/
~/src/svn2cl-0.7/svn2cl.sh --html --group-by-day file:///home/fox/prog/depot/trunk/pytimeout/
svn -m "Changelog update" commit ChangeLog ChangeLog.html
