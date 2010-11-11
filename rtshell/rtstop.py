#!/usr/bin/env python
# -*- Python -*-
# -*- coding: utf-8 -*-

'''rtshell

Copyright (C) 2009-2010
    Geoffrey Biggs
    RT-Synthesis Research Group
    Intelligent Systems Research Institute,
    National Institute of Advanced Industrial Science and Technology (AIST),
    Japan
    All rights reserved.
Licensed under the Eclipse Public License -v 1.0 (EPL)
http://www.opensource.org/licenses/eclipse-1.0.txt

rtstop library.

'''


from optparse import OptionParser, OptionError
from os import sep as pathsep
from os.path import splitext
from rtctree.component import Component
from rtctree.path import parse_path
from rtctree.tree import create_rtctree
from rtsprofile.rts_profile import RtsProfile
import sys

from rtshell import RTSH_VERSION
from rtshell.actions import *
from rtshell.rts_exceptions import RequiredActionFailedError
from rtshell.options import Options
from rtshell.plan import Plan


def deactivate_actions(rtsprofile):
    deactivates = []
    for comp in rtsprofile.components:
        for ec in comp.execution_contexts:
            deactivates.append(DeactivateCompAct(pathsep + comp.path_uri,
                comp.id, comp.instance_name, ec.id))
    return deactivates


def main(argv=None, tree=None):
    usage = '''Usage: %prog [options] [RTSProfile specification file]
Stop an RT system using an RT system profile specified in XML or YAML.

The input format will be determined automatically from the file extension.
If the file has no extension, the input format is assumed to be XML.
The output format can be over-ridden with the --xml or --yaml options.

If no file is given, the profile is read from standard input.'''
    parser = OptionParser(usage=usage, version=RTSH_VERSION)
    parser.add_option('--dry-run', dest='dry_run', action='store_true',
            default=False,
            help="Print what will be done but don't actually do anything. \
[Default: %default]")
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
            default=False, help='Verbose output. [Default: %default]')
    parser.add_option('-x', '--xml', dest='xml', action='store_true',
            default=True, help='Use XML input format if no extension. \
[Default: %default]')
    parser.add_option('-y', '--yaml', dest='xml', action='store_false',
            help='Use YAML input format if no extension. \
[Default: %default]')

    if argv:
        sys.argv = [sys.argv[0]] + argv
    try:
        options, args = parser.parse_args()
    except OptionError, e:
        print >>sys.stderr, 'OptionError: ', e
        return 1
    Options().verbose = options.verbose

    # Load the profile
    if len(args) == 1:
        # Read from a file
        ext = splitext(args[0])[1]
        # If the extension is yaml, force yaml mode. Otherwise assume XML or
        # whatever the user set with an option.
        if ext == '.yaml':
            options.xml = False
        with open(args[0]) as f:
            if options.xml:
                rtsprofile = RtsProfile(xml_spec=f)
            else:
                rtsprofile = RtsProfile(yaml_spec=f)
    elif not args:
        # Read from standard input
        lines = sys.stdin.read()
        if options.xml:
            rtsprofile = RtsProfile(xml_spec=lines)
        else:
            rtsprofile = RtsProfile(yaml_spec=lines)
    else:
        print >>sys.stderr, usage
        return 1

    # Build a list of actions to perform that will stop the system
    deactivates = deactivate_actions(rtsprofile)
    plan = Plan()
    plan.make(rtsprofile, deactivates, rtsprofile.deactivation,
            Component.INACTIVE)
    if options.dry_run:
        print plan
    else:
        if not tree:
            # Load the RTC Tree, using the paths from the profile
            tree = create_rtctree(paths=[parse_path(pathsep + c.path_uri)[0] \
                                            for c in rtsprofile.components])
        try:
            result = plan.execute(tree)
        except RequiredActionFailedError, e:
            print >>sys.stderr, e
            plan.cancel()
            return 1
        if result:
            print >>sys.stderr, 'Error executing plan'
            print >>sys.stderr, result
            return 1
    return 0


# vim: tw=79

