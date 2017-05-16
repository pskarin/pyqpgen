#!/bin/bash

WS=$1
LIBNAME=$2;
MODE=$3
VERSION=1;

if [ -e qp_files/data_struct.h ];
then
	VERSION=2;
fi;

if [ ${MODE} == "pxd" ]; then
	cat > ${WS}/pyqpgen-data.h <<__END
#include "pyqpgen-constants.h"
typedef struct __PyQPgenData {
	double target[(NUM_STATES + NUM_INPUTS) * HORIZON];
	double x0[NUM_STATES];
	double result[(NUM_STATES + NUM_INPUTS) * HORIZON];
	int num_iterations;
} PyQPgenData;

PyQPgenData * allocate();
void deallocate(PyQPgenData ** o);

double * target(PyQPgenData * o);
double * x0(PyQPgenData * o);
int * num_iterations(PyQPgenData * o);
double * result(PyQPgenData * o);
__END
	cat > ${WS}/pyqpgen-data.c <<__END
#include "pyqpgen-data.h"
#include <stdlib.h>

PyQPgenData * allocate() {
	return (PyQPgenData *) calloc(1, sizeof(PyQPgenData));
}
void deallocate(PyQPgenData ** o) {
	free(*o);
	*o = NULL;
}

double * target(PyQPgenData * o) { return &o->target[0]; }
double * x0(PyQPgenData * o) { return &o->x0[0]; }
int * num_iterations(PyQPgenData * o) { return &o->num_iterations; }
double * result(PyQPgenData * o) { return &o->result[0];; }
__END
	cp pyqpgen/pyqpgen.pxd.v${VERSION} ${WS}/${LIBNAME}.pxd
else
	cat pyqpgen/pyqpgen.pyx.v${VERSION} | sed "s/cimport pyqpgen as qpgen/cimport ${LIBNAME} as qpgen/" > ${WS}/${LIBNAME}.pyx
fi