#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2013 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Script harness for running OMERO.scripts locally within python


import omero
import omero.scripts
from omero.rtypes import wrap, unwrap, rstring, rlong


orig_client = omero.scripts.client


def setup():
    if not os.getenv('ICE_CONFIG'):
        raise Exception('ICE_CONFIG must be set')
    client = omero.client()
    return client


def set_inputs(client, params):
    ss = client.getSession().getSessionService()
    sid = client.getSessionId()
    for k, v in params.iteritems():
        ss.setInput(sid, k, wrap(v))


def get_client_wrapper(params):
    def client_wrapper(*args, **kwargs):
        print 'client_wrapper'
        client = orig_client(*args, **kwargs)
        set_inputs(client, params)
        return client
    return client_wrapper


def run(scriptfunc, params):
    try:
        omero.scripts.client = get_client_wrapper(params)
        if callable(scriptfunc):
            scriptfunc()
        elif hasattr(scriptfunc, 'runScript'):
            getattr(scriptfunc, 'runScript')()
        else:
            raise Exception('Unable to execute script function')
    finally:
        omero.scripts.client = orig_client


def example():
    try:
        reload(Hadoop_Example)
    except NameError:
        import Hadoop_Example
    params = { 'Data_Type': 'Image', 'IDs': [37960] }
    #params = { 'Data_Type': 'Dataset', 'IDs': [6552] }
    run(Hadoop_Example, params)

# E.g. In IPython shell
# execfile('script_harness.py')
# example()
