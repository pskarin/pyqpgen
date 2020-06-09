% Sampling period
MPC.h = 0.05;

% Dynamics (sampled at 20 Hz)
MPC.Adyn = [0.9993 -3.0083 -0.1131 -1.6081;
           -0.0000  0.9862  0.0478  0.0000;
            0.0000  2.0833  1.0089 -0.0000;
            0.0000  0.0526  0.0498  1.0000];
MPC.Bdyn = [-0.0804 -0.6347;-0.0291 -0.0143;
            -0.8679 -0.0917;-0.0216 -0.0022];

% specify cost
MPC.Q = diag([0,100,0,100]);
MPC.R = 0.01*eye(2);

% indicate that linear cost is parametric
MPC.gt = 1;

% specify soft state constraints
MPC.Cx = [0 1 0 0;0 0 0 1];
MPC.X.Ub = [0.5;100];
MPC.X.Lb = -[0.5;100];
MPC.Xf.Ub = [0.1,1];
MPC.Xf.Lb = -[0.1,1];

MPC.X.soft = [1e5;1e5];

% specify hard input constraints
MPC.Cu = eye(2);
MPC.U.Ub = [25;25];
MPC.U.Lb = -[25;25];

% control horizon
MPC.N = 3;

% decrease optimality tolerance
opts.rel_tol = 1e-4;
