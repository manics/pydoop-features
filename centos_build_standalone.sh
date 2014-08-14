#!/bin/sh

# Build a standalone archive for CentOS 6 so wndcharm can be run without
# additional system libraries

# WND_CHARM requirements: libtiff (which requires libjpeg-turbo) and fftw
# scipy requires atlas
# matplotlib requires freetype


yum install -y wget unzip zip
yum install -y \
        http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
yum install -y python-virtualenv yum-utils

yum install -y gcc-c++ swig git

useradd omero
su - omero

VENV=venv-wndcharm

virtualenv $VENV
source $VENV/bin/activate

mkdir tmp
pushd tmp
RPMS="fftw.x86_64 libtiff.x86_64 numpy.x86_64 scipy.x86_64 atlas.x86_64 \
    libgfortran.x86_64 libjpeg-turbo.x86_64 numpy-f2py.x86_64 \
    python-devel.x86_64 python-nose.noarch python-setuptools.noarch \
    suitesparse.x86_64 python-argparse.noarch"
DEVELRPMS="fftw-devel.x86_64 libtiff-devel.x86_64"
#MATPLOTLIBRPMS="python-matplotlib.x86_64 atk.x86_64 atlas.x86_64 \
#    avahi-libs.x86_64 cairo.x86_64 cups-libs.x86_64 fontconfig.x86_64 \
#    freetype.x86_64 gnutls.x86_64 gtk2.x86_64 jasper-libs.x86_64 \
#    libX11.x86_64 libXau.x86_64 libXcomposite.x86_64 libXcursor.x86_64 \
#    libXdamage.x86_64 libXext.x86_64 libXfixes.x86_64 libXft.x86_64 \
#    libXi.x86_64 libXinerama.x86_64 libXrandr.x86_64 libXrender.x86_64 \
#    libgfortran.x86_64 libjpeg-turbo.x86_64 libpng.x86_64 libtasn1.x86_64 \
#    libthai.x86_64 libtiff.x86_64 libxcb.x86_64 numpy.x86_64 pango.x86_64 \
#    pixman.x86_64 pkgconfig.x86_64 pycairo.x86_64 shared-mime-info.x86_64 \
#    dejavu-fonts-common.noarch dejavu-sans-fonts.noarch \
#    fontpackages-filesystem.noarch hicolor-icon-theme.noarch \
#    libX11-common.noarch python-dateutil.noarch python-nose.noarch pytz.noarch"
#yumdownloader $RPMS $DEVELRPMS $MATPLOTLIBRPMS
yumdownloader $RPMS $DEVELRPMS
for rpm in *.rpm; do
    rpm2cpio $rpm | cpio -ivd
done

export PYTHONPATH=~/tmp/usr/lib64/python2.6/site-packages:~/tmp/usr/lib/python2.6/site-packages
export LD_LIBRARY_PATH=~/tmp/usr/lib64:~/tmp/usr/lib64/atlas

export LIBRARY_PATH=~/tmp/usr/lib64
export CPATH=~/tmp/usr/include

pip install git+https://github.com/colettace/wnd-charm.git@unrequire_matplotlib
#pip install git+https://github.com/wnd-charm/wnd-charm.git

mv usr ~/$VENV/


pip freeze

cat << EOF > ~/$VENV/example.py
import numpy as np
import wndcharm
from wndcharm.FeatureSet import Signatures
from wndcharm.PyImageMatrix import PyImageMatrix

def features(img_arr):
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
    return fts

x = np.random.rand(30, 40)
f = features(x)
print f.names
print f.values
EOF

python ~/$VENV/example.py

cat << EOF > ~/$VENV/environment.settings
export PYTHONPATH=usr/lib64/python2.6/site-packages:usr/lib/python2.6/site-packages
export LD_LIBRARY_PATH=usr/lib64:usr/lib64/atlas
EOF

popd
zip -r $VENV.zip $VENV
