#!/bin/bash

WS=$1;
LIBNAME=$2;
MODE=$3;

if [ -e ${WS}/qp_files/data_struct.h ];
then
	QPFUNC="extern void qp(struct DATA * d, double *x_out, int *iter, double *gt, double *bt);";
	HINCLUDE="#include \"data_struct.h\"";
	CINCLUDE="extern void init_data(struct DATA *d); extern void free_data(struct DATA *d);";
	# Unfortunatelly, QPgen frees the input pointer in free_data although init_data does not allocate it. Therefore we
	# must allocate a new data struct all the time. We keep the pointer with the PyQPgenData struct anyway and hope to either
	# fix the free in QPgen, write a custom free or find that the data is constant and can be allocated once.
	DATAMEMBER="struct DATA * data;";
	RUNIMP="  o->data = malloc(sizeof(struct DATA)); init_data(o->data); qp(o->data, o->result, &o->num_iterations, o->target, o->x0); free_data(o->data);";
else
	QPFUNC="extern void qp(double *x_out, int *iter, double *gt, double *bt);";
	HINCLUDE="";
	CINCLUDE="";
	DATAMEMBER="";
	RUNIMP="  qp(o->result, &o->num_iterations, o->target, o->x0);";
fi;

if [ ${MODE} == "pxd" ]; then
	cat > ${WS}/pyqpgen-wrap.h <<__END
#include "pyqpgen-constants.h"
${HINCLUDE}
typedef struct __PyQPgenData {
	double target[(NUM_STATES + NUM_INPUTS) * HORIZON];
	double x0[NUM_STATES];
	double result[(NUM_STATES + NUM_INPUTS) * HORIZON];
	int num_iterations;
	double x1[NUM_STATES];
	${DATAMEMBER}
} PyQPgenData;

PyQPgenData * allocate();
void deallocate(PyQPgenData ** o);

double * target(PyQPgenData * o);
double * x0(PyQPgenData * o);
int * num_iterations(PyQPgenData * o);
double * result(PyQPgenData * o);
double * x1(PyQPgenData * o);

void sim(PyQPgenData * o);

void run(PyQPgenData * o);
__END
	cat > ${WS}/pyqpgen-wrap.c <<__END
#include "pyqpgen-wrap.h"
#include <stdlib.h>

${CINCLUDE}

${QPFUNC}

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

void run(PyQPgenData * o) {
${RUNIMP}
}

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
	cat pyqpgen/pyqpgen.pxd.template > ${WS}/${LIBNAME}.pxd
else
	cat pyqpgen/pyqpgen.pyx.template | sed "s/#LIBNAME/${LIBNAME}/" > ${WS}/${LIBNAME}.pyx
fi