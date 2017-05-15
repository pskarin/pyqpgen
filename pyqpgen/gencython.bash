#!/bin/bash

LIBNAME=$1;
VERSION=1;

if [ -e qp_files/data_struct.h ];
then
	VERSION=2;
fi;

cp pyqpgen/pyqpgen.pxd.v${VERSION} .ws/${LIBNAME}.pxd
cat pyqpgen/pyqpgen.pyx.v${VERSION} | sed "s/cimport pyqpgen as qpgen/cimport ${LIBNAME} as qpgen/" > .ws/${LIBNAME}.pyx
