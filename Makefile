include config.mk

.PHONY : default qpgen

CFLAGS=-Iqp_files -fPIC
CFLAGS += $(shell pkg-config --cflags python)

OUTPUT=$(LIBNAME).so

$(shell mkdir -p .ws)

default: qplib

# These are the files genrated in step 1 when pyqpgen/generate.m is run.
QPGENFILES=qp_files/ .ws/pyqpgen-constants.h qp_mex.mexa64

# First thing that needs to be done is to generate QPgen files from the user.m
# system specification. This is done throught the pyqpgen/generate.m matlab
# script which also creates a header file with constants.
qp_files/QPgen.c: user.m pyqpgen/generate.m
	matlab -nodisplay -nojvm -nodesktop -nosplash -r "addpath pyqpgen;generate"

# This part reads the source files genrated by QPgen. Depending on the system
# specification they may differ which is why they are dynamically fetched. This
# also means that they are not available in the first run and therefore there
# is an indirection through the qplib rule in which the makefile calls itself.
QPSOURCE=$(filter-out %/alg_data.c %/qp_mex.c,\
	$(shell find qp_files -iname '*.c' 2>/dev/null))
QPOBJ=$(QPSOURCE:.c=.o)

qplib: qp_files/QPgen.c
	@$(MAKE) -C . $(OUTPUT)

# This is where we enter when the make file has called itself from the qplib
# rule. So far QPgen has been executed through matlab and all C code is ready.
# Now compile relevant files in qp_files and generate .ws/{lib}.so using
# Cython then merge this into the final library.
$(OUTPUT): $(QPOBJ) .ws/$(LIBNAME).o
	$(LD) -shared $^ -o $(OUTPUT)


PXDVERSIONS=pyqpgen/pyqpgen.pxd.v1 pyqpgen/pyqpgen.pxd.v2
PYXVERSIONS=pyqpgen/pyqpgen.pyx.v1 pyqpgen/pyqpgen.pyx.v2
PXDOUT=.ws/$(LIBNAME).pxd
PYXOUT=.ws/$(LIBNAME).pyx
CYTHONOUT=.ws/$(LIBNAME).c

# pyqpgen/precython.bash copies and manipulates the templates for .pxd and
# .pyx files pyqpgen/ to .ws/.
$(PXDOUT): $(PXDVERSIONS)
	@bash pyqpgen/precython.bash $(LIBNAME) pxd

# pyqpgen/precython.bash copies and manipulates the templates for .pxd and
# .pyx files pyqpgen/ to .ws/.
$(PYXOUT): $(PYXVERSIONS)
	@bash pyqpgen/precython.bash $(LIBNAME) pyx

# Runs Cython on files located in .ws/.
$(CYTHONOUT): $(PXDOUT) $(PYXOUT)
	cython -o $(CYTHONOUT) $(PYXOUT)

.PHONY : clean cleanqpgen cleancc cleancython cleanlib

# Clean the artifacts from pyqpgen/generate.m
cleanqpgen:
	rm -rf $(QPGENFILES)

# Clean the artifacts from gcc compilation
cleancc:
ifdef $(QPOBJ)
	rm -f $(QPOBJ)
endif
	rm -f .ws/$(LIBNAME).o

# Clean the stuff created by and generated for Cython
cleancython:
	@rm -f $(PYXOUT) $(PXDOUT) $(CYTHONOUT)
	
# Remove the final library
cleanlib:
	@rm -f $(OUTPUT)

# Clean everything
clean: cleanqpgen cleancc cleancython cleanlib
	@rmdir .ws
