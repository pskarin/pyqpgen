addpath ../qpgen
user
% run code generator
[QP_reform,alg_data] = run_code_gen_MPC(MPC,opts);

fid = fopen('pyqpgen-constants.h', 'w');
fprintf(fid, '#define NUM_STATES %d\n',size(MPC.Adyn,1));
fprintf(fid, '#define NUM_INPUTS %d\n',size(MPC.Bdyn,2));
fprintf(fid, '#define HORIZON %d\n',MPC.N);
fprintf(fid, '#define ADATA {');
for i=1:size(MPC.Adyn, 1)
	for j=1:size(MPC.Adyn, 2)
		if i == 1 && j == 1
			fprintf(fid, '%f', MPC.Adyn(i,j));
		else
			fprintf(fid, ', %f', MPC.Adyn(i,j));
		end
	end
end
fprintf(fid, '}\n');
fprintf(fid, '#define BDATA {');
for i=1:size(MPC.Bdyn, 1)
	for j=1:size(MPC.Bdyn, 2)
		if i == 1 && j == 1
			fprintf(fid, '%f', MPC.Bdyn(i,j));
		else
			fprintf(fid, ', %f', MPC.Bdyn(i,j));
		end
	end
end
fprintf(fid, '}\n');
fclose(fid);

quit
