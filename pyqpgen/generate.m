addpath ../qpgen
addpath ../pyqpgen
user
% run code generator
opts.proj_name = getenv('QPPROJ')
[QP_reform,alg_data] = run_code_gen_MPC(MPC,opts);

fid = fopen('pyqpgen-constants.h', 'w');
fprintf(fid, '#include <float.h>\n');
fprintf(fid, '#define NUM_STATES %d\n',size(MPC.Adyn,1));
fprintf(fid, '#define NUM_INPUTS %d\n',size(MPC.Bdyn,2));
fprintf(fid, '#define NUM_OUTPUTS %d\n',size(MPC.Cx,1));
fprintf(fid, '#define SAMPLE_RATE %d\n',round(1/MPC.h));
fprintf(fid, '#define HORIZON %d\n',MPC.N);
fprintf(fid, '#define MAX_ITERATIONS %d\n',opts.max_iter);
fprintf(fid, '#define TOLERANCE %e\n',opts.rel_tol);
pdouble(fid, 'ADATA', MPC.Adyn);
pdouble(fid, 'BDATA', MPC.Bdyn);
pdouble(fid, 'QDATA', MPC.Q);
pdouble(fid, 'RDATA', MPC.R);
pdouble(fid, 'CxDATA', MPC.Cx);
pdouble(fid, 'XUbDATA', MPC.X.Ub);
pdouble(fid, 'XLbDATA', MPC.X.Lb);
pdouble(fid, 'XSoftDATA', MPC.X.soft);
pdouble(fid, 'CuDATA', MPC.Cu);
pdouble(fid, 'UUbDATA', MPC.U.Ub);
pdouble(fid, 'ULbDATA', MPC.U.Lb);
pdouble(fid, 'USoftDATA', MPC.U.soft);
fclose(fid);

quit
