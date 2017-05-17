include .config
CONFIG?=example.mk
$(shell echo CONFIG=$(CONFIG) > .config)
include $(CONFIG)

WS=.ws-$(LIBNAME)

.PHONY : default qpgen inform

CFLAGS=-I$(WS)/qp_files -I$(WS) -fPIC
CFLAGS += $(shell pkg-config --cflags python)

OUTPUT=$(LIBNAME).so

$(shell mkdir -p $(WS))

default: inform qplib

inform:
	@echo '>>>> Using config $(CONFIG) <<<<<'

# These are the files genrated in step 1 when pyqpgen/generate.m is run.
QPGENFILES=$(WS)/qp_files/ $(WS)/pyqpgen-constants.h $(WS)/qp_mex.mexa64 $(WS)/user.m

# First thing that needs to be done is to generate QPgen files from the m-file
# system specification. This is done throught the pyqpgen/generate.m matlab
# script which also creates a header file with constants.
$(WS)/qp_files/QPgen.c: $(MFILE) pyqpgen/generate.m
	cp $(MFILE) $(WS)/user.m
	cd $(WS) && SYSFILE=$(MFILE) matlab -nodisplay -nojvm -nodesktop -nosplash -r "addpath ../pyqpgen;generate"

# This part reads the source files genrated by QPgen. Depending on the system
# specification they may differ which is why they are dynamically fetched. This
# also means that they are not available in the first run and therefore there
# is an indirection through the qplib rule in which the makefile calls itself.
QPSOURCE=$(filter-out %/alg_data.c %/qp_mex.c,\
$(shell find $(WS)/qp_files -iname '*.c' 2>/dev/null))
QPOBJ=$(QPSOURCE:.c=.o)

qplib: $(WS)/qp_files/QPgen.c
	@$(MAKE) -C . $(OUTPUT)

# This is where we enter when the make file has called itself from the qplib
# rule. So far QPgen has been executed through matlab and all C code is ready.
# Now compile relevant files in qp_files and generate $(WS)/{lib}.so using
# Cython then merge this into the final library.
$(OUTPUT): $(QPOBJ) $(WS)/$(LIBNAME).o $(WS)/pyqpgen-data.o
	$(LD) -shared $^ -o $(OUTPUT)


PXDVERSIONS=pyqpgen/pyqpgen.pxd.v1 pyqpgen/pyqpgen.pxd.v2
PYXVERSIONS=pyqpgen/pyqpgen.pyx.v1 pyqpgen/pyqpgen.pyx.v2
PXDOUT=$(WS)/$(LIBNAME).pxd
PYXOUT=$(WS)/$(LIBNAME).pyx
CYTHONOUT=$(WS)/$(LIBNAME).c

# pyqpgen/precython.bash copies and manipulates the templates for .pxd and
# .pyx files pyqpgen/ to $(WS)/.
$(PXDOUT): $(PXDVERSIONS) pyqpgen/precython.bash
	@bash pyqpgen/precython.bash $(WS) $(LIBNAME) pxd

# pyqpgen/precython.bash copies and manipulates the templates for .pxd and
# .pyx files pyqpgen/ to $(WS)/.
$(PYXOUT): $(PYXVERSIONS) pyqpgen/precython.bash
	@bash pyqpgen/precython.bash $(WS) $(LIBNAME) pyx

# Runs Cython on files located in $(WS)/.
$(CYTHONOUT): $(PXDOUT) $(PYXOUT)
	cython -o $(CYTHONOUT) $(PYXOUT)

.PHONY : clean cleanqpgen cleancc cleancython cleanlib

# Clean the artifacts from pyqpgen/generate.m
cleanqpgen:
	rm -rf $(QPGENFILES)

# Clean the artifacts from gcc compilation
cleancc:
ifneq ($(strip $(QPOBJ)),)
	rm -f $(QPOBJ)
endif
	rm -f $(WS)/$(LIBNAME).o

# Clean the stuff created by and generated for Cython
cleancython:
	@rm -f $(PYXOUT) $(PXDOUT) $(CYTHONOUT)
	@rm -f $(WS)/pyqpgen-data.c
	@rm -f $(WS)/pyqpgen-data.h
	@rm -f $(WS)/pyqpgen-data.o
	
# Remove the final library
cleanlib:
	@rm -f $(OUTPUT)

# Clean everything
clean: cleanqpgen cleancc cleancython cleanlib
	@rmdir $(WS)
