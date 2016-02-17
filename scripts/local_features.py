# BEGIN_COPYRIGHT
#
# Copyright (C) 2014-2015 CRS4.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# END_COPYRIGHT

"""
Local feature calculation with wnd-charm (for comparison).
"""

import sys
import os
import warnings
import subprocess

try:
    from pyavroc import AvroFileReader, AvroFileWriter
except ImportError:
    from pyavroc_emu import AvroFileReader, AvroFileWriter
    warnings.warn("pyavroc not found, using standard avro lib\n")

from bioimg import BioImgPlane
from feature_calc import calc_features, to_avro


def get_schema(basename):
    scripts_dir = os.path.abspath(os.path.dirname(__file__))
    repo_root = os.path.dirname(scripts_dir)
    fn = os.path.join(repo_root, "src", "main", "avro", basename)
    if not os.path.exists(fn):
        old_pwd = os.getcwd()
        try:
            os.chdir(repo_root)
            subprocess.call("mvn compile", shell=True)
        finally:
            os.chdir(old_pwd)
    return fn


def main(argv):
    try:
        avro_fn = argv[1]
    except IndexError:
        sys.exit('Usage: python %s avro_fn' % argv[0])

    with open(get_schema('Signatures.avsc')) as f:
        out_schema = f.read()

    tag, ext = os.path.splitext(os.path.basename(avro_fn))
    out_fn = '%s_features%s' % (tag, ext)
    print 'writing to %s' % out_fn
    with open(out_fn, 'w') as fout:
        writer = AvroFileWriter(fout, out_schema)
        with open(avro_fn) as fin:
            reader = AvroFileReader(fin)
            for r in reader:
                p = BioImgPlane(r)
                print 'input shape:', p.pixel_data.shape
                pixels = p.get_xy()
                plane_tag = '%s-z%04d-c%04d-t%04d' % (p.name, p.z, p.c, p.t)
                print '  processing %s' % plane_tag
                features = calc_features(pixels, plane_tag)
                out_rec = to_avro(features)
                out_rec['plane_tag'] = plane_tag
                writer.write(out_rec)
        writer.close()


if __name__ == '__main__':
    main(sys.argv)
