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
	double x1[NUM_STATES];
} PyQPgenData;

PyQPgenData * allocate();
void deallocate(PyQPgenData ** o);

double * target(PyQPgenData * o);
double * x0(PyQPgenData * o);
int * num_iterations(PyQPgenData * o);
double * result(PyQPgenData * o);
double * x1(PyQPgenData * o);

void sim(PyQPgenData * o);
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
double * result(PyQPgenData * o) { return &o->result[0]; }
double * x1(PyQPgenData * o) { return &o->x1[0]; }

static const double matA[] = ADATA;
static const double matB[] = BDATA;

void sim(PyQPgenData * o) {
	int i,j,xa,xb;
	double * x0 = &o->x0[0];
	double * x1 = &o->x1[0];
	double * u0 = &o->result[NUM_STATES*HORIZON];
	for (i = 0, xa = 0, xb = 0; i < NUM_STATES; i++) {
		double v = 0;
		for (j = 0; j < NUM_STATES; j++, xa++) {
			v += matA[xa]*x0[j];
		}
		for (j = 0; j < NUM_INPUTS; j++, xb++) {
			v += matB[xb]*u0[j];
		}
		x1[i] = v;
	}
}
__END
	cp pyqpgen/pyqpgen.pxd.v${VERSION} ${WS}/${LIBNAME}.pxd
else
	cat pyqpgen/pyqpgen.pyx.v${VERSION} | sed "s/cimport pyqpgen as qpgen/cimport ${LIBNAME} as qpgen/" > ${WS}/${LIBNAME}.pyx
fi