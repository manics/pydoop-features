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

#
#

import omero
from omero import scripts
from omero.rtypes import rstring, rlong, unwrap
from datetime import datetime
from itertools import chain

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import export_image_planes
import try_features


def export_planes(client, dataType, ids, exportdir):
    a = '-' + dataType[0].lower()
    args = list(chain(*((a, str(i)) for i in ids)))
    args += ['-o', exportdir]
    args = export_image_planes.parse_args(args)
    #if args.verbose:
    #    log.setLevel(logging.DEBUG)

    with export_image_planes.Connection(detach=True, client=client) as c:
        objects = c.objectGenerator(args.ordered_arguments)
        for im in c.imageGenerator(objects):
            #log.info('Image: %d', im.id)
            export_image_planes.writeplanes(
                c.client, im, args.output_dir, args)


def calculate(exportdir, calculatedir):
    return try_features.main(exportdir, calculatedir)


def runScript():
    """
    The main entry point of the script
    """

    client = scripts.client(
        'Hadoop_Example.py',
        'Export some image planes and calculate features',

        scripts.String(
            'Data_Type', optional=False, grouping='1',
            description='The data you want to work with.',
            values=[rstring('Project'), rstring('Dataset'), rstring('Image')],
            default='Dataset'),

        scripts.List(
            'IDs', optional=False, grouping='1',
            description='List of Project, Dataset IDs or Image IDs').ofType(
            rlong(0)),

        version = '0.0.1',
        authors = ['Simon Li', 'OME Team'],
        institutions = ['University of Dundee'],
        contact = 'ome-devel@lists.openmicroscopy.org.uk',
    )

    try:
        startTime = datetime.now()
        session = client.getSession()
        client.enableKeepAlive(60)
        message = ''

        # process the list of args above.
        scriptParams = client.getInputs(unwrap=True)
        print scriptParams

        dataType = scriptParams['Data_Type']
        ids = scriptParams['IDs']
        exportdir = omero.util.temp_files.gettempdir() / 'imageplanes'
        calculatedir = omero.util.temp_files.gettempdir() / 'features'

        print 'Exporting planes to %s' % exportdir
        export_planes(client, dataType, ids, exportdir)
        print 'Calculating features to %s' % calculatedir
        hdfs_out_dir = calculate(exportdir, calculatedir)

        stopTime = datetime.now()
        message += 'Features saved to HDFS directory: %s\n' % hdfs_out_dir
        message += 'Duration: %s' % str(stopTime - startTime)

        print message
        client.setOutput('Message', rstring(str(message)))

    finally:
        client.closeSession()

if __name__ == '__main__':
    runScript()
