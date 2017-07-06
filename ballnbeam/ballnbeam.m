% Continous time ball and beam without friction or noise
% x0: position
% x1: speed
% x2: beam angle
% u0: angular velocity
%
% Note that the beam position is defined such that a positive angle will cause the ball to roll in the negative direction.

g = 9.80665;
fc = 5/7;
d = 0.1; 
A = [ 0 1 0; 0 0 -g*fc; 0 0 0];
B = [ 0; 0; d];

% Sampled at 25ms
h = 0.025;
PhiGamma = expm([A B; zeros(1,length(A)) 0]*h);
MPC.Adyn = PhiGamma(1:length(A),1:length(A));
MPC.Bdyn = PhiGamma(1:length(A),length(A)+1);
MPC.h = h;

% Costs
MPC.Q = diag([400, 50, 0]);
MPC.R = 0.25;
MPC.N = 60;

% Must be set
MPC.gt = 1;

% State limits.
MPC.Cx = [1 0 0; 0 0 1];
MPC.X.Ub = [0.55;1];
MPC.X.Lb = -MPC.X.Ub;
MPC.X.soft = [inf;1e5];

% Input restrictions.
MPC.Cu = [1];
MPC.U.Ub = [44];
MPC.U.Lb = -[44];
MPC.U.soft = [];

opts.max_iter = 500
opts.rel_tol = 1e-3;

