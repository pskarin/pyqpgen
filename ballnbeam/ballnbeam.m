% Continous time ball and beam without friction or noise
% x0: position
% x1: speed
% x2: beam angle
% u0: angular velocity
%
% Note that the beam position is defined such that a positive angle will cause the ball to roll in the negative direction.

BEAM_LENGTH = 1.1;
g = 9.80665;

g1 = 0.44;
g2 = 10/(pi/4);
g3 = g;
g4 = 5/7;
g5 = 10/(BEAM_LENGTH/2);

g34 = -g3*g4;

A = [ 0 1 0; 0 0 g34; 0 0 0];
B = [ 0; 0; g1];
C = [ g5 0 0; 0 0 g2];
% Sampled at 50ms
h = 0.05;
dsys = c2d(ss(A, B, C, []), h);
MPC.Adyn = dsys.A;
MPC.Bdyn = dsys.B;
MPC.h = h;

% Costs
MPC.Q = diag([400, 5, 0]);
MPC.R = 0.25;
MPC.N = 40;
[K,S,e] = lqr(dsys, MPC.Q, MPC.R);
%MPC.Qf = S;

% Must be set
MPC.gt = 1;

% State limits.
MPC.Cx = [1 0 0; 0 1 0; 0 0 1];
MPC.X.Ub = [0.55; 10; pi/4];
MPC.X.Lb = -MPC.X.Ub;
%MPC.Xf.Ub = [0.1; 0.1; pi/30];
%MPC.Xf.Lb = -MPC.Xf.Ub;
%MPC.X.soft = [inf; 1e5];
MPC.X.soft = [];

% Input restrictions.
MPC.Cu = [1];
MPC.U.Ub = [10];
MPC.U.Lb = -[10];
MPC.U.soft = [];

opts.max_iter = 500
opts.rel_tol = 1e-3;

