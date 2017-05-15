.PHONY : all nogui clean

default: qp_files/QPgen.c

qp_files/QPgen.c: user.m pyqpgen/generate.m
	matlab -nodisplay -nojvm -nodesktop -nosplash -r "addpath pyqpgen;generate"

clean :
	@rm -f qp_mex.mexa64
	@rm -rf qp_files

