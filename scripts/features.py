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
import numpy as np
#import time
from StringIO import StringIO

import pydoop.hdfs as hdfs
import pydoop.utils as utils

import os
import sys
sys.path.append(os.path.expanduser(
    '~/work/wnd-charm/build/lib.macosx-10.9-x86_64-2.7'))

import pychrm
from pychrm.FeatureSet import Signatures
from pychrm.PyImageMatrix import PyImageMatrix


def pychrm_small_features(img_arr):
    assert len(img_arr.shape) == 2
    pychrm_matrix = PyImageMatrix()
    pychrm_matrix.allocate(img_arr.shape[0], img_arr.shape[1])
    numpy_matrix = pychrm_matrix.as_ndarray()

    numpy_matrix[:] = img_arr
    feature_plan = pychrm.StdFeatureComputationPlans.getFeatureSet()
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
    out_dir = conf.get('out.dir', utils.make_random_str())
    if not hdfs.path.isdir(out_dir):
        hdfs.mkdir(out_dir)
        hdfs.chmod(out_dir, 'g+rwx')
    img_path = record.strip()
    a = get_array(img_path)
    out_a = calc_features(a)
    out_path = hdfs.path.join(out_dir, '%s.out' % hdfs.path.basename(img_path))
    #out_path = hdfs.path.join(out_dir, '%s.out-%d' % (
    #    hdfs.path.basename(img_path), time.time() * 1000))
    with hdfs.open(out_path, 'w') as fo:
        np.save(fo, out_a)  # actual output
    hdfs.chmod(out_path, 'g+rw')
    writer.emit(img_path, fo.name)  # info (tab-separated input-output)
