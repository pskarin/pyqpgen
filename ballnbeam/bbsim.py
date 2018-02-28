import math
import convert
import threading
import time
import posix_ipc as ipc
import sys
import select

G = 9.80665*5.0/7.0
MAX_ANGLE = math.pi

# Does a Euler approximation of the ball and beam system
class BBSim:
  def __init__(self, beamlength=1.1, netdelay=0, stepIterations=100, coulombFrictionFactor=0.0):
    """ beamlength is the length of the beam in meters
        maxspeed is the radians that the beam moves in one second.
        netdelay is the number of samples to delay, not the delay time!
    """
    self.maxspeed = 45
    self.cf = coulombFrictionFactor
    self.stepIterations = stepIterations
    self.netdelay = netdelay
    self.posmax = beamlength/2

    self.reset()

  def reset(self):
    self.u = 0                # The input signal on the writers end
    self.theta = 0            # The beam angle
    self.speed = 0            # The ball speed
    self.position = 0         # The ball position
    self.sampledPosition = 0  # The position on the readers end of the network
    self.uQueue = []
    self.sampleQueue = []
    for i in range(0, self.netdelay):
      self.uQueue.append(0)
      self.sampleQueue.append(0)    

  def printState(self):
    print("BBSim u: {:0.2f}, theta: {:0.2f}, speed: {:0.2f}, position: {:0.2f}".format(self.u, self.theta, self.speed, self.position))

  def getBallPositionRange(self):
    return (-self.posmax, self.posmax)

  def getBeamSpeedRange(self):
    return (-2*math.pi, 2*math.pi)

  def getBeamAngleRange(self):
    return (-math.pi/4, math.pi/4)

  def getBeamAngle(self):
    return self.theta

  def getBallPosition(self):
    return self.sampledPosition

  def setState(self, ballposition=0, ballspeed=0, beamangle=0):
    self.position = ballposition
    self.speed = ballspeed
    self.theta = beamangle
    
    self.sampledPosition = ballposition
    self.sampleQueue = []
    for i in range(0, self.netdelay): self.sampleQueue.append(ballposition)

  def setBeamSpeed(self, s):
    self.u = min(self.maxspeed, abs(s))
    if s < 0: self.u = -self.u

  def getBeamSpeed(self):
    return self.u

  # Update theta. Input u is rad/sec
  def evolveTheta(self, theta, u, sec):
    theta = min(MAX_ANGLE, max(-MAX_ANGLE, theta+u*sec))
    return theta
  
  def evolveSpeed(self, theta, speed, sec):
    pull=-math.sin(theta)
    friction=min(abs(pull), self.cf*math.cos(theta))
    if pull < 0:
      friction = -friction
    accel = G*(pull-friction)
    speed += accel*sec
    return speed

  def evolvePosition(self, speed, position, sec):
    return position + speed*sec

  def step(self, sec):
    self.uQueue.append(self.u)
    u = self.uQueue.pop()
    s = sec/self.stepIterations
    for i in range(1, self.stepIterations):
      self.speed = self.evolveSpeed(self.theta, self.speed, s)  # Set the acceleration of the ball
      self.position = self.evolvePosition(self.speed, self.position, s)
      self.theta = self.evolveTheta(self.theta, u, s)       # Set the angle of beam after 'sec'
    self.sampleQueue.append(self.position)
    self.sampledPosition = self.sampleQueue.pop(0)

class BBSimIPC:
  def __init__(self, id=0):
    self.ang = ipc.MessageQueue("/bbsim_out1-{}".format(id), flags=ipc.O_CREAT, max_messages=1)
    self.pos = ipc.MessageQueue("/bbsim_out2-{}".format(id), flags=ipc.O_CREAT, max_messages=1)
    self.write = ipc.MessageQueue("/bbsim_in-{}".format(id), flags=ipc.O_CREAT, max_messages=1)
    self._reset = ipc.MessageQueue("/bbsim_reset-{}".format(id), flags=ipc.O_CREAT, max_messages=1)    
    self.reset()

  def reset(self):
    try:
      self._reset.send("{}".format(1))
      self.angle = 0
      self.position = 0
      self.speed = 0    
    except ipc.BusyError:
      print("Failed to send reset, check your code, this ought to not happen")

  def getBeamAngle(self):
    try:
      message, priority = self.ang.receive(0) # Get input signal
      self.angle = float(message)
    except ipc.BusyError:
      pass
    return self.angle

  def getBallPosition(self):
    try:
      message, priority = self.pos.receive(0) # Get input signal
      self.position = float(message)
    except ipc.BusyError:
      pass
    return self.position

  def setBeamSpeed(self, angular):
      self.speed = angular
      try:
        self.write.send("{}".format(angular))
      except ipc.BusyError:
        print("Failed to set new input, this should not happen")

  def getBeamSpeed(self):
    return self.speed

  def getBallPositionRange(self):
    return (-0.55, 0.55)

  def getBeamSpeedRange(self):
    return (-2*math.pi, 2*math.pi)

  def getBeamAngleRange(self):
    return (-math.pi/4, math.pi/4)

  def setState(self, ballposition=0, ballspeed=0, beamangle=0):
    pass

  def step(self, h):
    pass
      
def runsim(bbsim, qin, qout1, qout2, qreset, period, id):
    global _lock
    global _state

    t=period
    next = time.time()+t
    infoDump=int(0.5/t)
    infoDumpCnt = 0
    input = 0
    inpoll = select.poll()
    inpoll.register(sys.stdin, select.POLLIN)
    while True:
      try:
        message, priority = qin.receive(0) # Get input signal
        input = float(message)
        bbsim.setBeamSpeed(input)
      except ipc.BusyError:
        pass

      # Check reset command
      reset = True
      try: 
        qreset.receive(0) # If there is a message then reset
      except ipc.BusyError: reset = False
      pollevents = inpoll.poll(0)
      if len(pollevents) > 0 and pollevents[0][1] == select.POLLIN:
        reset = True
      if reset:
        print("RESET")
        sys.stdin.readline()
        bbsim.reset()
        infoDumpCnt = infoDump-1
      else:
        bbsim.step(t)

      try: qout1.receive(0) # Queue is of size one, clear pending message
      except ipc.BusyError: pass
      try: qout2.receive(0) # Queue is of size one, clear pending message
      except ipc.BusyError: pass
 
      angle = bbsim.getBeamAngle()
      pos = bbsim.getBallPosition()
      speed = bbsim.getBeamSpeed()
 
      qout1.send("{}".format(angle), timeout=0) # Write message, queue is guranteed to be empty
      qout2.send("{}".format(pos), timeout=0) # Write message, queue is guranteed to be empty
      _lock.acquire()
      _state[id] = {'angle': angle, 'pos': pos, 'speed': speed}
      _lock.release()
    
      time.sleep(max(0, next-time.time()))
      next += t

import os
import argparse
import threading
import time
import signal

global _lock
global _state
global _sigint

def sig_int_handler(signum, frame):
  global _sigint
  _sigint(signum, frame)

def thread_main(id, h):
  qout1 = ipc.MessageQueue("/bbsim_out1-{}".format(id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
  qout2 = ipc.MessageQueue("/bbsim_out2-{}".format(id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
  qin = ipc.MessageQueue("/bbsim_in-{}".format(id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
  qreset = ipc.MessageQueue("/bbsim_reset-{}".format(id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
  runsim(BBSim(), qin, qout1, qout2, qreset, h, id)

if __name__ == "__main__":
  global _sigint
  parser = argparse.ArgumentParser(description='Ball n Beam simulation')
  parser.add_argument('-c', '--plants', type=int, default=1,
                  help='Number of ball and beam plants')
  parser.add_argument('-t', '--period', type=int, default=1,
                    help='Update interval in milliseconds (default 1 ms)')
  args = parser.parse_args()

  _sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, sig_int_handler)

  os.umask(0)
  _lock = threading.Lock()
  _state = []
  for x in range(0, args.plants):
    _state.append({'angle': 0, 'pos': 0, 'speed': 0})
  for x in range(0, args.plants):    
    th = threading.Thread(target=thread_main, args=(x, float(args.period)/1000.0))
    th.setDaemon(True)
    th.start()
  starttime = time.time()
  while True:
    _lock.acquire()
    print("Uptime: {}".format(int(time.time()-starttime)))
    for x in range(0, args.plants):
      print("\033[0K[Plant {}] pos: {:6.3f}, angle: {:6.3f}, velo: {:6.3f}".format(x, _state[x]['pos'],  _state[x]['angle'],  _state[x]['speed']))
    sys.stdout.write("\033[{}A".format(args.plants+1))
    _lock.release()
    time.sleep(0.25)