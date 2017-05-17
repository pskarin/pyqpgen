#!/usr/bin/env python

import sys
sys.path.append("qpexample-out")
from qpexample import QP

import time
import numpy as np
import matplotlib.pyplot as plt

qp = QP()
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
	
	x0 = qp.sim()
	qp.setState(x0)

	maxtime = max(maxtime, t2-t1)
	sumtime += t2-t1
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
	
