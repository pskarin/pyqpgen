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
	double * states;
	double * inputs;
	double * outputs;
	double data[PYQPGEN_NUM_STATES + PYQPGEN_NUM_INPUTS + PYQPGEN_NUM_OUTPUTS];
} PyQPgenData;
PyQPgenData * PyQPgenAllocate();
void PyQPgenDeallocate(PyQPgenData ** o);
double * PyQPgen_getInputs(PyQPgenData * o);
double * PyQPgen_getOutputs(PyQPgenData * o);
double * PyQPgen_getStates(PyQPgenData * o);
__END
	cat > ${WS}/pyqpgen-data.c <<__END
#include "pyqpgen-data.h"
#include <stdlib.h>
PyQPgenData * PyQPgenAllocate() {
	PyQPgenData * o = (PyQPgenData *) calloc(1, sizeof(PyQPgenData));
	o->states = &o->data[0];
	o->inputs = &o->data[PYQPGEN_NUM_STATES];
	o->outputs = &o->data[PYQPGEN_NUM_STATES+PYQPGEN_NUM_INPUTS];
	return o;
}
void PyQPgenDeallocate(PyQPgenData ** o) {
	free(*o);
	*o = NULL;
}
double * PyQPgen_getInputs(PyQPgenData * o) { return o->inputs; }
double * PyQPgen_getOutputs(PyQPgenData * o) { return o->outputs; }
double * PyQPgen_getStates(PyQPgenData * o) { return o->states; }

__END
	cp pyqpgen/pyqpgen.pxd.v${VERSION} ${WS}/${LIBNAME}.pxd
else
	cat pyqpgen/pyqpgen.pyx.v${VERSION} | sed "s/cimport pyqpgen as qpgen/cimport ${LIBNAME} as qpgen/" > ${WS}/${LIBNAME}.pyx
fi