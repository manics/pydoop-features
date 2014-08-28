# BEGIN_COPYRIGHT
#
# Copyright (C) 2014 CRS4.
#
# This file is part of pydoop-features.
#
# pydoop-features is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pydoop-features is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pydoop-features.  If not, see <http://www.gnu.org/licenses/>.
#
# END_COPYRIGHT

"""
Pydoop script for image feature calculation.

On some systems this may be run as the mapred system user
"""
from StringIO import StringIO


# mapred.cache.archives libs.tgz must contain the contents of libs/
# without the parent directory (and should therefore contain a __init__.py
# file):
# tar -zcvf libs.tgz -C libs .


import os
import sys


IMPORTS_FAILED = None

try:
    import numpy as np

    import pydoop.hdfs as hdfs
    import pydoop.utils as utils

    import wndcharm
    from wndcharm.FeatureSet import Signatures
    from wndcharm.PyImageMatrix import PyImageMatrix
except ImportError as e:
    print e
    print '\n'.join(sys.path)
    print os.listdir('.')
    for a in os.walk('venv-wndcharm'):
        print '%s\n%s' % (a[0], '\n\t'.join(a[2]))
    for kv in os.environ.iteritems():
        print '%s=%s' % kv
    IMPORTS_FAILED = e
    raise


def pychrm_small_features(img_arr):
    assert len(img_arr.shape) == 2
    pychrm_matrix = PyImageMatrix()
    pychrm_matrix.allocate(img_arr.shape[1], img_arr.shape[0])
    numpy_matrix = pychrm_matrix.as_ndarray()

    numpy_matrix[:] = img_arr
    feature_plan = wndcharm.StdFeatureComputationPlans.getFeatureSet()
    options = ""  # Wnd-charm options
    fts = Signatures.NewFromFeatureComputationPlan(
        pychrm_matrix, feature_plan, options)

    # fts.{names, values, version}
    return fts.values


def basic_intensity_stats(img_arr):
    return [img_arr.min(), img_arr.max(), img_arr.mean()]


def get_array(path):
    # Read file manually to avoid c++ type errors between numpy and hdfs
    with hdfs.open(path) as f:
        s = StringIO(f.read())
        return np.load(s)


def calc_features(img_arr):
    # return basic_intensity_stats(img_arr)
    return pychrm_small_features(img_arr)


def mapper(_, record, writer, conf):
    if IMPORTS_FAILED:
        print IMPORTS_FAILED
        raise IMPORTS_FAILED

    try:
        from libs import pkg
    except Exception as e:
        print e
        print sys.path
        print os.listdir('.')
        print os.listdir(sys.path[0])
        raise

    out_dir = conf.get('out.dir', utils.make_random_str())
    if not hdfs.path.isdir(out_dir):
        hdfs.mkdir(out_dir)
        hdfs.chmod(out_dir, 'g+rwx')
    img_path = record.strip()
    a = get_array(img_path)
    out_a = calc_features(a)
    out_path = hdfs.path.join(out_dir, '%s.out' % hdfs.path.basename(img_path))
    with hdfs.open(out_path, 'w') as fo:
        np.save(fo, out_a)  # actual output
    hdfs.chmod(out_path, 'g+rw')
    writer.emit(img_path, fo.name)  # info (tab-separated input-output)
