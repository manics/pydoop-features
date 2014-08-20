#!/bin/sh

[ $# -eq 1 ] || {
	echo Hadoop server IP required
	exit 1
}

IP="$1"

CONFD=conf.run
rm -rf "$CONFD"

cp -a conf.template "$CONFD"
sed -i.bak -e "s/%HADOOP%/$IP/" "$CONFD/core-site.xml" "$CONFD/mapred-site.xml"

