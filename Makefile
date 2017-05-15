include config.mk

.PHONY : default qpgen clean

CFLAGS=-Iqp_files -fPIC
CFLAGS += $(shell pkg-config --cflags python)

OUTPUT=$(LIBNAME).so

$(shell mkdir -p .ws)

default: qplib

qpgen: qp_files/QPgen.c 

QPSOURCE=$(filter-out %/alg_data.c %/qp_mex.c,$(shell find qp_files -iname '*.c'))
QPOBJ=$(QPSOURCE:.c=.o)

qplib: qpgen 
	@$(MAKE) -C . $(OUTPUT)
	
$(OUTPUT): $(QPOBJ) .ws/$(LIBNAME).o
	$(LD) -shared $^ -o $(OUTPUT)
	
qp_files/QPgen.c: user.m pyqpgen/generate.m
	matlab -nodisplay -nojvm -nodesktop -nosplash -r "addpath pyqpgen;generate"

.ws/$(LIBNAME).pxd: pyqpgen/pyqpgen.pxd.v1 pyqpgen/pyqpgen.pxd.v2
	bash pyqpgen/gencython.bash $(LIBNAME)
	
.ws/$(LIBNAME).pyx: .ws/$(LIBNAME).pxd pyqpgen/pyqpgen.pyx.v1 pyqpgen/pyqpgen.pyx.v2

.ws/$(LIBNAME).c: .ws/$(LIBNAME).pxd .ws/$(LIBNAME).pyx
	cython -o .ws/$(LIBNAME).c .ws/$(LIBNAME).pyx

clean1:
	@rm -f $(OUTPUT)
	@rm -rf qp_files/*.o
	@rm -rf .ws

clean: clean1
	@rm -f qp_mex.mexa64
	@rm -rf qp_files

