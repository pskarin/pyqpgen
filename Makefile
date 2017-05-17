include .config
CONFIG?=example.mk
$(shell echo CONFIG=$(CONFIG) > .config)
include $(CONFIG)

CONFIGDIR=$(shell dirname $(CONFIG))

MFILE:=$(CONFIGDIR)/$(MFILE)

WS=.ws-$(LIBNAME)

.PHONY : default qpgen inform

CFLAGS=-I$(WS)/qp_files -I$(WS) -fPIC
CFLAGS += $(shell pkg-config --cflags python)

ifeq ($(strip $(CONFIGDIR)),.)
OUTDIR=$(LIBNAME)-out
OUTPUT=$(OUTDIR)/$(LIBNAME).so
else
OUTDIR=$(CONFIGDIR)/out
OUTPUT=$(OUTDIR)/$(LIBNAME).so
endif

$(shell mkdir -p $(WS) $(OUTDIR))

default: inform qplib

inform:
	@echo '>>>>> Using config $(CONFIG) <<<<<'
	@echo '>>>>> Output goes into $(CONFIGDIR)/ <<<<<'

# These are the files genrated in step 1 when pyqpgen/generate.m is run.
QPGENFILES=$(WS)/qp_files/ $(WS)/pyqpgen-constants.h $(WS)/qp_mex.mexa64 $(WS)/user.m

# First thing that needs to be done is to generate QPgen files from the m-file
# system specification. This is done throught the pyqpgen/generate.m matlab
# script which also creates a header file with constants.
$(WS)/qp_files/QPgen.c: $(MFILE) pyqpgen/generate.m
	cp $(MFILE) $(WS)/user.m
	cd $(WS) && SYSFILE=$(MFILE) matlab -nodisplay -nojvm -nodesktop -nosplash -r "addpath ../pyqpgen;generate"
	mkdir -p $(OUTDIR)/qp_files
	cp -r $(WS)/qp_files/qp_data $(OUTDIR)/qp_files/

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
$(OUTPUT): $(QPOBJ) $(WS)/$(LIBNAME).o $(WS)/pyqpgen-wrap.o
	$(LD) -shared $^ -o $(OUTPUT)


PXDTEMPLATE=pyqpgen/pyqpgen.pxd.template
PYXTEMPLATE=pyqpgen/pyqpgen.pyx.template
PXDOUT=$(WS)/$(LIBNAME).pxd
PYXOUT=$(WS)/$(LIBNAME).pyx
CYTHONOUT=$(WS)/$(LIBNAME).c

# pyqpgen/precython.bash copies and manipulates the templates for .pxd and
# .pyx files pyqpgen/ to $(WS)/.
$(PXDOUT): $(PXDTEMPLATE) pyqpgen/precython.bash
	bash pyqpgen/precython.bash $(WS) $(LIBNAME) pxd $(WITHSIM)

# pyqpgen/precython.bash copies and manipulates the templates for .pxd and
# .pyx files pyqpgen/ to $(WS)/.
$(PYXOUT): $(PYXTEMPLATE) pyqpgen/precython.bash
	bash pyqpgen/precython.bash $(WS) $(LIBNAME) pyx $(WITHSIM)

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
	@rm -f $(WS)/pyqpgen-wrap.c
	@rm -f $(WS)/pyqpgen-wrap.h
	@rm -f $(WS)/pyqpgen-wrap.o
	
# Remove the final library
cleanlib:
	@rm -f $(OUTPUT)

# Clean everything
clean: cleanqpgen cleancc cleancython cleanlib
	@rmdir $(WS)
