.PHONY : all nogui clean

CFLAGS=-Iqp_files -fPIC

default: qplib

qpgen: qp_files/QPgen.c 


QPSOURCE=$(filter-out %/alg_data.c %/qp_mex.c,$(shell find qp_files -iname '*.c'))
QPOBJ=$(QPSOURCE:.c=.o)

qplib: qpgen 
	$(MAKE) -C . _qplib
	
_qplib: $(QPOBJ)
	$(LD) -shared $^ -o lib.so
		
qp_files/QPgen.c: user.m pyqpgen/generate.m
	matlab -nodisplay -nojvm -nodesktop -nosplash -r "addpath pyqpgen;generate"

clean :
	@rm -f qp_mex.mexa64
	@rm -rf qp_files

