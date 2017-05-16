#!/usr/bin/env python

import sys
sys.path.append(".")
import example

import time
import numpy as np
import matplotlib.pyplot as plt

A = np.array([0.9993, -3.0083, -0.1131, -1.6081,
             -0.0000,  0.9862,  0.0478,  0.0000,
              0.0000,  2.0833,  1.0089, -0.0000,
              0.0000,  0.0526,  0.0498,  1.0000]).reshape((4,4))

B = np.array([-0.0804, -0.6347,
              -0.0291, -0.0143,
              -0.8679, -0.0917,
			  -0.0216, -0.0022]).reshape((4, 2))

qp = example.QP()
qp.setTargetStates(np.tile([0,-1000,0,-1000], 10))
qp.setTargetInputs(np.zeros(20))
x0 = np.zeros(4)

sumitr = 0
maxitr = 0
maxtime = 0
sumtime = 0

U = np.zeros((2, 100))
Y = np.zeros((2, 100))
for i in range(0, 100):
	if i == 50:
		qp.setTargetStates(np.zeros(40))

	t1 = time.time()
	u0 = qp.run()
	t2 = time.time()
	maxtime = max(maxtime, t2-t1)
	sumtime += t2-t1
	x0 = A.dot(x0)+B.dot(u0)
	
	qp.setState(x0)
	sumitr += qp.getNumberOfIterations()
	maxitr = max(maxitr, qp.getNumberOfIterations())
	U[:,i] = u0
	Y[0,i] = x0[1]
	Y[1,i] = x0[3]
	
plt.subplot(221)
plt.plot(Y[0,:])
plt.subplot(223)
plt.plot(Y[1,:])
plt.subplot(222)
plt.plot(U[0,:])
plt.subplot(224)
plt.plot(U[1,:])

print("Average number of iterations: {}".format(sumitr/100.0))
print("Maximum number of iterations: {}".format(maxitr))
print("Average execution time: {} ms".format((sumtime*1000)/100))
print("Maximum execution time: {} ms".format(maxtime*1000))
plt.show()
	
