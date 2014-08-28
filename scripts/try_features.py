#!/usr/bin/env python

import datetime as dt
import os
import subprocess
import sys

import pydoop.hdfs as hdfs
# import pydoop.utils as utils

# Number of mappers. See also mapred.tasktracker.map.tasks.maximum in
# mapred-site.xml
MR_TASKS = 2
# PYDOOP_EXE = os.path.join(os.path.expanduser('~'), '.local', 'bin', 'pydoop')
PYDOOP_EXE = 'pydoop'

OPTS = ['--num-reducers=0',
        '--no-override-env',
        '-D', 'mapred.map.tasks=%d' % MR_TASKS,
        '--log-level', 'DEBUG']
#HADOOP_OPTS = ['-archives', 'libs.tgz']

LOCAL_PREFIX = 'venv-wndcharm/venv-wndcharm'
LD_LIBRARY_PATH = 'usr/lib64:usr/lib64/atlas'
PYTHONPATH = ':'.join([
    'lib/python2.6/site-packages',
    'usr/lib64/python2.6/site-packages',
    'usr/lib/python2.6/site-packages'])


def prefix_paths(prefix, paths):
    sep = os.path.pathsep
    return sep.join(os.path.join(prefix, p) for p in paths.split(sep))


HADOOP_ENV = {
    'LD_LIBRARY_PATH': prefix_paths(LOCAL_PREFIX, LD_LIBRARY_PATH),
    'PYTHONPATH': prefix_paths(LOCAL_PREFIX, PYTHONPATH),
    }
HADOOP_OPTS = [
    '-D',
    'mapred.child.env=' + ','.join(
        '%s=%s' % kv for kv in HADOOP_ENV.iteritems())
   ]


ARCHIVES = ['venv-wndcharm.zip']

def get_archive_args(archives):
    ars = []
    for a in archives:
        name = os.path.basename(a)
        sym = os.path.splitext(name)[0]
        ars.append(name + '#' + sym)
    return ['-D', 'mapred.cache.archives=%s' % ','.join(ars)]

OPTS.extend(get_archive_args(ARCHIVES))

ENV_OVERRIDE = {}
#ENV_OVERRIDE = {
#    'HADOOP_CONF_DIR': '/Users/simon/work/pydoop-features/scripts/conf.run',
#    'HADOOP_USER_NAME': 'omero',
#    'CLASSPATH': None,
#    }

def timestamp_str():
    return dt.datetime.now().strftime('%Y%m%d-%H%M%S')


def chmodr(path, fmode, dmode=None):
    if dmode is None:
        dmode = fmode
    if hdfs.path.isdir(path):
        # lsl lists the contents of the dir
        hdfs.chmod(path, dmode)
    for p in hdfs.lsl(path, recursive=True):
        if p['kind'] == 'directory':
            hdfs.chmod(p['name'], dmode)
        else:
            hdfs.chmod(p['name'], fmode)


def main(local_in, local_out=None):
    ts = timestamp_str()
    in_dir = 'in-%s' % ts
    mr_in = 'mr-%s.in' % ts
    out_dir = 'out-%s' % ts
    mr_out = 'mr-%s.out' % ts

    print 'Local input dir:', local_in
    print 'HDFS input dir:', in_dir
    print 'HDFS output dir:', out_dir
    print 'MapReduce input file:', mr_in
    print 'MapReduce output file:', mr_out

    # The OMERO CLASSPATH causes problems with Hadoop
    #for kv in os.environ.iteritems():
    #    print '%s=%s' % kv

    hdfs.cp(hdfs.path.join('file:', os.path.abspath(local_in)), in_dir)
    chmodr(in_dir, 'a+rx')
    for ar in ARCHIVES:
        dst = os.path.basename(ar)
        try:
            hdfs.rmr(dst)
        except IOError:
            pass
        hdfs.cp(hdfs.path.join('file:', os.path.abspath(ar)), '.')

    with hdfs.open(mr_in, 'w') as mrf:
        for f in hdfs.lsl(in_dir, recursive=True):
            if f['kind'] == 'file':
                mrf.write('%s\n' % f['name'])

    hdfs.mkdir(out_dir)
    hdfs.chmod(out_dir, 'a+rwx')

    opts = OPTS + ['-D', 'out.dir=%s' % out_dir] + HADOOP_OPTS
    cmd = [PYDOOP_EXE, 'script'] + opts + ['features.py'] + [mr_in, mr_out]

    env = os.environ.copy()
    env.update(ENV_OVERRIDE)

    print 'Running %s' % cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print 'stdout:\n%s\n\nstderr:\n%s\n' % (stdout, stderr)

    if not local_out:
        local_out = os.path.basename(out_dir)
    local_out = os.path.abspath(local_out)
    hdfs.cp(out_dir, hdfs.path.join('file:', local_out))
    return out_dir


if __name__ == '__main__':
    main(*sys.argv[1:])
