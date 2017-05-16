addpath qpgen
user
% run code generator
[QP_reform,alg_data] = run_code_gen_MPC(MPC,opts);

fid = fopen('.ws/pyqpgen-constants.h', 'w');
fprintf(fid, '#define PYQPGEN_NUM_STATES %d\n',size(MPC.Adyn,1));
fprintf(fid, '#define PYQPGEN_NUM_INPUTS %d\n',size(MPC.Bdyn,2));
fprintf(fid, '#define PYQPGEN_NUM_OUTPUTS %d\n',size(MPC.Cx,1));
fprintf(fid, '#define PYQPGEN_HORIZON %d\n',MPC.N);
fclose(fid);
quit
