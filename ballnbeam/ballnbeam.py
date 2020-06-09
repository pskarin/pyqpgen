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

#sim = bbsim.BBSim(netdelay=0, stepIterations=100)
sim = bbsim.BBSimInterfacePosixShm()


sim.set_state(ballposition=x[0], ballspeed=x[1], beamangle=x[2])

U = []
P = []
T = []
S = []
X = []

resetbeam = True

raw_input("Resetting beam. Press enter.")
waitUntil = time.time()+h
for x in range(sampleRate*2):
    angle = sim.get_angle()
    if abs(angle) < 0.01:
        break
    bb.setState([0, 0, angle])
    u0 = bb.run()
    sim.set_beam_speed(u0[0])
    print("Angle: {} rad".format(angle))
    time.sleep(max(0, waitUntil-time.time()))
    waitUntil += h
sim.set_beam_speed(0)

raw_input("Ready. Press enter.")
waitUntil = time.time()+h
tsum = 0
tpos = 0
prevpos=None

for i in range(iterations):

    t1 = time.time() 

    print("Read full state")
    angle = sim.get_angle()
    position = sim.get_position()
    speed = sim.get_ball_speed()

    prevpos = position
    tpos = t1
    bb.setState([position, speed, angle])
    r = np.array((0.55*setpointDefs[setpointIndex]['value']/10, 0, 0))
    bb.setTargetState(r)

    # Run the optimization
    u0 = bb.run()
 #   print(bb.getFullControlVector())

    traj = np.array(bb.getFullStateVector()).reshape(bb.horizon(),3).T
    endstate = np.abs(traj[:,-1])
#    print(endstate < np.array([0.1, 2, np.pi/4]))
#    print(traj)
#    MPC.Xf.Ub = [0.1; 2; pi/4];
#    print(np.array(bb.getFullControlVector()))
 
    # Apply input
    if bb.getNumberOfIterations() < bb.maxIterations():
      sim.set_beam_speed(u0[0])

    t2 = time.time()
    tsum += t2-t1

    if i == setpointDefs[setpointIndex]['end']:
        setpointIndex += 1
    X.append(float(i)/sampleRate)
    U.append(u0[0])
    P.append(position)
    S.append(speed)
    T.append(angle)

  
    print("{:4.2f} ({:3d}) Angle: {:6.3f} rad, Position: {:5.3f} m, Speed: {:5.3f} m/s, U: {:5.2f} rad/s, Itr: {}".
        format(float(i)/sampleRate, int((t2-t1)*1000), angle, position, speed, convert.v2angular(u0[0]), bb.getNumberOfIterations()))
  
    sim.step(h)

    time.sleep(max(0, waitUntil-time.time()))
    waitUntil += h

sim.set_beam_speed(0)

print("Average time: {}".format(tsum/iterations))

plt.subplot(221)
plt.plot(X,U)
plt.title('Input')
plt.ylim((-11, 11))
plt.ylabel('rad/s')

plt.subplot(222)
plt.plot(X,P)
plt.title('Position')
plt.ylim(np.array(sim.get_position_range())*1.1)
plt.ylabel('m')

plt.subplot(223)
plt.plot(X,S)
plt.title('Speed')
plt.ylim((-1, 1))
plt.ylabel('m/s')

plt.subplot(224)
plt.plot(X,T)
plt.title('Theta')
plt.ylim(np.array(sim.get_angle_range())*1.1)
plt.ylabel('rad')

plt.show()
