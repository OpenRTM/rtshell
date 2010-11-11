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

rtteardown library.

'''


from optparse import OptionParser, OptionError
from os import sep as pathsep
from os.path import splitext
from rtctree.path import parse_path
from rtctree.tree import create_rtctree
from rtsprofile.rts_profile import RtsProfile
import sys

from rtshell import RTSH_VERSION
from rtshell.actions import *
from rtshell.rts_exceptions import RequiredActionFailedError
from rtshell.options import Options


def disconnect_actions(rtsprofile):
    disconnects = []
    for conn in rtsprofile.data_port_connectors:
        source_comp = rtsprofile.find_comp_by_target(conn.source_data_port)
        source_path = pathsep + source_comp.path_uri
        source_port = conn.source_data_port.port_name
        prefix = source_comp.instance_name + '.'
        if source_port.startswith(prefix):
            source_port = source_port[len(prefix):]
        dest_comp = rtsprofile.find_comp_by_target(conn.target_data_port)
        dest_path = pathsep + dest_comp.path_uri
        dest_port =conn.target_data_port.port_name
        prefix = dest_comp.instance_name + '.'
        if dest_port.startswith(prefix):
            dest_port = dest_port[len(prefix):]
        disconnects.append(DisconnectPortsAct(source_path, source_port,
                                              dest_path, dest_port))

    for conn in rtsprofile.service_port_connectors:
        source_comp = rtsprofile.find_comp_by_target(conn.source_service_port)
        source_path = pathsep + source_comp.path_uri
        source_port = conn.source_service_port.port_name
        prefix = source_comp.instance_name + '.'
        if source_port.startswith(prefix):
            source_port = source_port[len(prefix):]
        dest_comp = rtsprofile.find_comp_by_target(conn.target_service_port)
        dest_path = pathsep + dest_comp.path_uri
        dest_port = conn.target_service_port.port_name
        prefix = dest_comp.instance_name + '.'
        if dest_port.startswith(prefix):
            dest_port = dest_port[len(prefix):]
        disconnects.append(DisconnectPortsAct(source_path, source_port,
                                              dest_path, dest_port))
    return disconnects


def main(argv=None, tree=None):
    usage = '''Usage: %prog [options] <RTSProfile specification file>
Destroy an RT system using an RT system profile specified in XML or YAML.

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

    # Build a list of actions to perform that will destroy the system
    actions = disconnect_actions(rtsprofile)
    if options.dry_run:
        for a in actions:
            print a
    else:
        if not tree:
            # Load the RTC Tree, using the paths from the profile
            tree = create_rtctree(paths=[parse_path(pathsep + c.path_uri)[0] \
                                            for c in rtsprofile.components])
        try:
            for a in actions:
                a(tree)
        except RequiredActionFailedError, e:
            print >>sys.stderr, e
            return 1
    return 0


# vim: tw=79

