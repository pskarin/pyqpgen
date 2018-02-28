#!/usr/bin/env python

import sys
sys.path.append('lib')
from qpballnbeam import *
import numpy as np
import matplotlib.pyplot as plt
import time
import bbsim
import convert
import math

if len(sys.argv) < 2:
  print("Must set at least one interval {setpoint},{seconds}")
  sys.exit(1)

bb = QP()
sampleRate = bb.getSampleRate()
h = 1.0/sampleRate

setpointIndex=0
setpointDefs=[]
iterations = 0
for i in range(1, len(sys.argv)):
  d = [ float(x) for x in str.split(sys.argv[i], ',') ]
  iterations += int(d[1]*sampleRate)
  setpointDefs.append({'end': iterations, 'value': d[0]})

print("A: {}".format(bb.getA()))
print("B: {}".format(bb.getB()))
print("h: {}".format(1.0/bb.getSampleRate()))

Q = np.array(bb.getQ()).reshape((bb.numStates(), bb.numStates()))

x = np.array([0, 0, 0])

#sim = bbsim.BBSim(netdelay=0, stepIterations=10)
sim = bbsim.BBSimIPC()

ctrl = sim

sim.setState(ballposition=x[0], ballspeed=x[1], beamangle=x[2])

U = []
P = []
T = []
S = []
X = []

resetbeam = True

raw_input("Resetting beam. Press enter.")
waitUntil = time.time()+h
for x in range(sampleRate*2):
    angle = ctrl.getBeamAngle()
    if abs(angle) < 0.01:
        break
    bb.setState([0, 0, angle])
    u0 = bb.run()
    ctrl.setBeamSpeed(u0[0])
    print("Angle: {} rad".format(angle))
    time.sleep(max(0, waitUntil-time.time()))
    waitUntil += h
ctrl.setBeamSpeed(0)

raw_input("Ready. Press enter.")
waitUntil = time.time()+h
tsum = 0
tpos = 0
prevpos=None

for i in range(iterations):

    t1 = time.time() 

    angle = ctrl.getBeamAngle()
    position = ctrl.getBallPosition()

    if prevpos is None:
        prevpos = position
        speed = 0
    else:
        newspeed = (position-prevpos)/(t1-tpos)
        if abs(newspeed - speed) > 0.19:
            speed += 9.80665*angle*(t1-tpos)
        else:
            speed = newspeed

    prevpos = position
    tpos = t1
    bb.setState([position, speed, angle])
 
    # Run the optimization
    u0 = bb.run()
    # Apply input
    ctrl.setBeamSpeed(u0[0])

    t2 = time.time()
    tsum += t2-t1

    if i == setpointDefs[setpointIndex]['end']:
        setpointIndex += 1
    X.append(float(i)/sampleRate)
    U.append(u0[0])
    P.append(position)
    S.append(speed)
    T.append(angle)

  
    x = bb.getState()
    print("{:4.2f} ({:3d}) Angle: {:6.2f} deg, Position: {:5.2f} m, Speed: {:5.2f} m/s, U: {:5.2f} rad/s".
        format(float(i)/sampleRate, int((t2-t1)*1000), convert.angle2deg(angle), position, speed, u0[0]))
  
    r = np.array((-setpointDefs[setpointIndex]['value']/20, 0, 0))
    bb.setTargetStates(np.tile(np.dot(Q, r), (bb.horizon(),1)).reshape(
        bb.numStates()*bb.horizon(), 1))

    sim.step(h)

    time.sleep(max(0, waitUntil-time.time()))
    waitUntil += h

ctrl.setBeamSpeed(0)

print("Average time: {}".format(tsum/iterations))

plt.subplot(221)
plt.plot(X,U)
plt.title('Input')
plt.ylim(ctrl.getBeamSpeedRange())
plt.ylabel('rad/s')

plt.subplot(222)
plt.plot(X,P)
plt.title('Position')
plt.ylim(ctrl.getBallPositionRange())
plt.ylabel('m')

plt.subplot(223)
plt.plot(X,S)
plt.title('Speed')
plt.ylim((-1, 1))
plt.ylabel('m/s')

plt.subplot(224)
plt.plot(X,T)
plt.title('Theta')
plt.ylim(ctrl.getBeamAngleRange())
plt.ylabel('rad')

plt.show()
