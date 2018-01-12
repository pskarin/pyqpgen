addpath ../qpgen
user
% run code generator
opts.proj_name = getenv('QPPROJ')
[QP_reform,alg_data] = run_code_gen_MPC(MPC,opts);

fid = fopen('pyqpgen-constants.h', 'w');
fprintf(fid, '#define NUM_STATES %d\n',size(MPC.Adyn,1));
fprintf(fid, '#define NUM_INPUTS %d\n',size(MPC.Bdyn,2));
fprintf(fid, '#define SAMPLE_RATE %d\n',round(1/MPC.h));
fprintf(fid, '#define HORIZON %d\n',MPC.N);
fprintf(fid, '#define ADATA {');
for i=1:size(MPC.Adyn, 1)
  for j=1:size(MPC.Adyn, 2)
    if i == 1 && j == 1
      fprintf(fid, '%e', MPC.Adyn(i,j));
    else
      fprintf(fid, ', %e', MPC.Adyn(i,j));
    end
  end
end
fprintf(fid, '}\n');
fprintf(fid, '#define BDATA {');
for i=1:size(MPC.Bdyn, 1)
  for j=1:size(MPC.Bdyn, 2)
    if i == 1 && j == 1
      fprintf(fid, '%e', MPC.Bdyn(i,j));
    else
      fprintf(fid, ', %e', MPC.Bdyn(i,j));
    end
  end
end
fprintf(fid, '}\n');
fprintf(fid, '#define QDATA {');
for i=1:size(MPC.Q, 1)
  for j=1:size(MPC.Q, 2)
    if i == 1 && j == 1
      fprintf(fid, '%e', MPC.Q(i,j));
    else
      fprintf(fid, ', %e', MPC.Q(i,j));
    end
  end
end
fprintf(fid, '}\n');
fprintf(fid, '#define RDATA {');
for i=1:size(MPC.R, 1)
  for j=1:size(MPC.R, 2)
    if i == 1 && j == 1
      fprintf(fid, '%e', MPC.R(i,j));
    else
      fprintf(fid, ', %e', MPC.R(i,j));
    end
  end
end
fprintf(fid, '}\n');
fclose(fid);

quit
