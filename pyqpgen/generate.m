addpath ../qpgen
user
% run code generator
[QP_reform,alg_data] = run_code_gen_MPC(MPC,opts);

fid = fopen('pyqpgen-constants.h', 'w');
fprintf(fid, '#define NUM_STATES %d\n',size(MPC.Adyn,1));
fprintf(fid, '#define NUM_INPUTS %d\n',size(MPC.Bdyn,2));
fprintf(fid, '#define HORIZON %d\n',MPC.N);
fclose(fid);

quit
