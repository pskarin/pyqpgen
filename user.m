Phi = [3.111 0.429 1 0 0 0 0 0 0 0;
    0.08268 2.794 0 1 0 0 0 0 0 0;
    -3.182 -0.9092 0 0 1 0 0 0 0 0;
    -0.2245 -2.631 0 0 0 1 0 0 0 0;
    0.8211 0.3671 0 0 0 0 1 0 0 0;
    0.1541 0.8153 0 0 0 0 0 1 0 0;
    0.455 0.2896 0 0 0 0 0 0 1 0;
    0.02951 0.06612 0 0 0 0 0 0 0 1;
    -0.2051 -0.1762 0 0 0 0 0 0 0 0;
    -0.04261 -0.04461 0 0 0 0 0 0 0 0;
    ];

Gamma = [0.0008364 -0.0004057;
    0.0008679 -0.0001901;
    0.0009015 -0.0009729;
    0.0006347 -0.00009547;
    0.001133 0.002063;
    -0.002024 0.0000549;
    -0.001292 -0.0003008;
    0.0003297 -0.0003316;
    0 0;
    0 0;
   ];

C = [1 0 0 0 0 0 0 0 0 0;
    0 1 0 0 0 0 0 0 0 0];


D = [0 0;
    0 0];

Phi2 = zeros(16,16);
Phi2(1:10,1:10) = Phi;
Phi2(11:16,11:16) = eye(6,6);
Phi2(1:10,13:14) = Gamma;
Phi2(1:2,15:16) = eye(2,2);

Gamma2 = zeros(16,2);
Gamma2(1:10,:) = Gamma;

C2 = zeros(2,16); 
C2(:,1:10) = C;
Cy = C2;
Cy(:,11:12) = eye(2,2);

D2 = D;

% Weights
Q = 1*diag([4 1 zeros(1,14)]);%1*diag([1,1]);
R = 5*diag([8 1]);%5*diag([4 1]);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% specify dynamics (sampled with 50 ms sampling time)
MPC.Adyn = Phi2;
MPC.Bdyn = Gamma2;

% specify cost
MPC.Q = Q;
MPC.R = R;

% indicate that linear cost is parametric
MPC.gt = 1;

% specify soft state constraints
%MPC.Cx = [0 1 0 0;0 0 0 1];
%MPC.X.Ub = [0.5;100];
%MPC.X.Lb = -[0.5;100];
%MPC.X.soft = [1e5;1e5];

% specify hard input constraints
MPC.Cu = eye(2);
u0 = [2.7 4.3]';
%u_max = [6 6]'- u0;
%u_min = -u0-[2,2]';
MPC.U.Ub = [10;10]-u0;
MPC.U.Lb = -u0;

% control horizon
MPC.N = 30;

% decrease optimality tolerance
opts.rel_tol = 1e-4;

%dlmwrite('phi.txt', Phi)
%dlmwrite('gamma.txt', Gamma)
%dlmwrite('phi2.txt', Phi2)
%dlmwrite('gamma2.txt', Gamma2)
%dlmwrite('c.txt', C)
%dlmwrite('c2.txt', C2)

