Pydoop Features
===============

An example of using Apache Hadoop to run processing jobs for [OMERO](https://github.com/openmicroscopy/openmicroscopy/). Work in progress.

The idea behind this project is to use [Pydoop](https://github.com/crs4/pydoop), a Python API for Hadoop, to transfer data in/out of a Hadoop cluster, and to calculate features using [WND-CHARM](https://github.com/wnd-charm/wnd-charm/) on multiple image planes.

The Hadoop_Example.py script is intended to ultimately work as an OMERO.script and can be run using script_harness.py. However, it will not currently work when launched by OMERO.server due to conflicts in the OMEOR and Hadoop classpath.

Also note that at present this requires a lot of custom setup and configuration.

Discussion list: <ome-devel@lists.openmicroscopy.org.uk>
