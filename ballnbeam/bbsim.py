#!/usr/bin/env python

import math
import convert
import threading
import time
import posix_ipc as ipc
import sys
import select
import mmap
import struct
import os

G = 9.80665*5.0/7.0
MAX_ANGLE = math.pi

# BALL AND BEAM SIMULATION PRIMITIVES
class BBSimBase(object):
  def __init__(self):
    pass

# Does a Euler approximation of the ball and beam system
class BBSimEuler(BBSimBase):
  def __init__(self, beamlength=1.1, netdelay=0, stepIterations=100, coulombFrictionFactor=0.0):
    """ beamlength is the length of the beam in meters
        maxspeed is the radians that the beam moves in one second.
        netdelay is the number of samples to delay, not the delay time!
    """
    BBSimBase.__init__(self)
    self.maxspeed = 4.4
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

  def getBallSpeed(self):
    return self.speed

  def setState(self, ballposition=0, ballspeed=0, beamangle=0):
    self.position = ballposition
    self.speed = ballspeed
    self.theta = beamangle
    
    self.sampledPosition = ballposition
    self.sampleQueue = []
    for i in range(0, self.netdelay): self.sampleQueue.append(ballposition)

  def setBeamSpeed(self, volt):
    self.u = min(self.maxspeed, abs(0.44*volt))
    if volt < 0: self.u = -self.u

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

class BBSim(BBSimEuler):
  """ Legacy class """
  def __init__(self, beamlength=1.1, netdelay=0, stepIterations=100, coulombFrictionFactor=0.0):
    BBSimEuler.__init__(self, beamlength, netdelay, stepIterations, coulombFrictionFactor)

# BALL AND BEAM SIMULATION INTERFACES
class BBSimInterface:
  def __init__(self, id=0):
    self.id = id

  def reset(self):
    pass

  def get_position_range(self):
    """ Get min and max ball position (left and right beam length) """
    return (-0.55, 0.55)

  def get_beam_velocity_range(self):
    """ Get min and max velocity of the beam """
    return (-2*math.pi, 2*math.pi)

  def get_angle_range(self):
    """ Get the min and max angle of the beam """
    return (-math.pi/4, math.pi/4)

  def get_state(self):
    """ Read the full state in one go (pos, speed, angle, u) """
    return (0,0,0,0)

  def get_angle(self):
    return 0

  def get_position(self):
    return 0

  def get_ball_speed(self):
    return 0

  def set_beam_speed(self, volt):
    pass

  def set_state(self, ballposition=0, ballspeed=0, beamangle=0):
    """ Legacy. TODO: Implement for IPC variants. """
    pass

  def step(self, h):
    pass

class MemMapped(object):
  """ Reads and writes data from mem-mapped file """
  def __init__(self, fid, lock):
    self.mm = mmap.mmap(fid, 0)
    self._lock = lock

  def lock(self):
    self._lock.acquire()

  def unlock(self):
    self._lock.release()

  def write_float(self, value, offset):
    self.mm.seek(offset)
    ba = bytearray(struct.pack('d', value))
    for b in ba:
      self.mm.write_byte(chr(b))

  def write_byte(self, value, offset):
    self.mm.seek(offset)
    self.mm.write_byte(chr(value))

  def read_float(self, offset):
    self.mm.seek(offset)
    ba = bytearray(8)
    for i in range(0, len(ba)):
      ba[i] = self.mm.read_byte()
    return struct.unpack('d', ba)[0]

  def read_byte(self, offset):
    self.mm.seek(offset)
    return ord(self.mm.read_byte())

    
class BBSimInterfacePosixShm(BBSimInterface):
  def __init__(self, id=0):
    BBSimInterface.__init__(self, id)
    self.lock = ipc.Semaphore("/bbsim_shm_lock-{}".format(id))
    self.shm = ipc.SharedMemory("/bbsim_shm-{}".format(id))
    self.mm = MemMapped(self.shm.fd, self.lock)

  def reset(self):
    self.mm.lock()
    self.mm.write_byte(1, 32)
    self.mm.unlock()

  def get_angle(self):
    self.mm.lock()
    val = self.mm.read_float(8)
    self.mm.unlock()
    return val

  def get_position(self):
    self.mm.lock()
    val = self.mm.read_float(16)
    self.mm.unlock()
    return val

  def set_beam_speed(self, volt):
    self.mm.lock()
    self.mm.write_float(volt, 0)
    self.mm.unlock()

  def get_ball_speed(self):
    self.mm.lock()
    val = self.mm.read_float(24)
    self.mm.unlock()
    return val

  def get_state(self):
    self.mm.lock()
    u = self.mm.read_float(0)
    angle = self.mm.read_float(8)
    pos = self.mm.read_float(16)
    speed = self.mm.read_float(24)
    self.mm.unlock()
    return (pos, angle, speed, u)


class BBSimInterfacePosixQueue(BBSimInterface):
  def __init__(self, id=0):
    BBSimInterface.__init__(self, id)
    self.ang = ipc.MessageQueue("/bbsim_out1-{}".format(id), max_messages=1)
    self.pos = ipc.MessageQueue("/bbsim_out2-{}".format(id), max_messages=1)
    self.write = ipc.MessageQueue("/bbsim_in-{}".format(id), max_messages=1)
    self._reset = ipc.MessageQueue("/bbsim_reset-{}".format(id), max_messages=1)    
    # Provides the possibility to read the state perfectly
    self.x2 = ipc.MessageQueue("/bbsim_ballspeed-{}".format(id), max_messages=1)
    self.angle = 0
    self.position = 0
    self.ballspeed = 0

  def reset(self):
    try:
      self._reset.send("{}".format(1))
    except ipc.BusyError:
      print("Failed to send reset, check your code, this ought to not happen")

  def get_angle(self):
    try:
      message, priority = self.ang.receive(0) # Get input signal
      self.angle = float(message)
    except ipc.BusyError:
      pass
    return self.angle

  def get_position(self):
    try:
      message, priority = self.pos.receive(0) # Get input signal
      self.position = float(message)
    except ipc.BusyError:
      pass
    return self.position

  def set_beam_speed(self, volt):
      try:
        self.write.send("{}".format(volt))
      except ipc.BusyError:
        print("Failed to set new input, this should not happen")

  def get_ball_speed(self):
    try:
      message, priority = self.x2.receive(0) # Get input signal
      self.position = float(message)
    except ipc.BusyError:
      pass
    return self.position


class BBSimIPC(BBSimInterfacePosixQueue):
  """ Legacy class """
  def __init__(self):
    BBSimInterfacePosixQueue.__init__(self)

  def getBallPositionRange(self):
    return self.get_position_range()

  def getBeamSpeedRange(self):
    return self.get_beam_velocity_range()

  def getBeamAngleRange(self):
    return self.get_angle_range()

  def getBeamAngle(self):
    return self.get_angle()

  def getBallPosition(self):
    return self.get_position()

  def setBeamSpeed(self, volt):
    return self.set_beam_speed(volt)

  def getBallSpeed(self):
    return self.get_ball_speed()

  def setState(self, ballposition=0, ballspeed=0, beamangle=0):
    pass

  def step(self, h):
    pass



# BALL AND BEAM SIMULATION ACTIVITIES

class BBSimActivityBase(object):
  def __init__(self, id):
    self.id = id
    self.u = 0

  def setup_communication(self):
    pass

  def read_input(self):
    """ Reads the control signal. This shall return the latest value again if no new input is available """
    return 0

  def write_output(self, position, angle, _ball_speed = 0):
    """ Set the output ports, i.e. the sensors to be read by client.
        For convenience the ball speed (x2) is provided so state can be
        perfectly recreated. """
    pass

  def is_reset(self):
    """ Check if reset signal is high """
    pass

  def run(self, bbsim, period, id):
    global _lock
    global _state

    t=period
    next = time.time()+t
    infoDump=int(0.5/t)
    infoDumpCnt = 0
    inpoll = select.poll()
    inpoll.register(sys.stdin, select.POLLIN)
    while True:
      bbsim.setBeamSpeed(self.read_input())

      # Check reset command
      reset = self.is_reset()
      # This checks if enter is pressed in which case a reset is also done
#      pollevents = inpoll.poll(0)
#      if len(pollevents) > 0 and pollevents[0][1] == select.POLLIN:
#        reset = True
      if reset:
#        sys.stdin.readline()
        bbsim.reset()
#        infoDumpCnt = infoDump-1
      else:
        bbsim.step(t) # Here new state is calculated

      angle = bbsim.getBeamAngle()
      pos = bbsim.getBallPosition()
      speed = bbsim.getBeamSpeed()

      self.write_output(pos, angle, bbsim.getBallSpeed())

      _lock.acquire()
      _state[id] = {'angle': angle, 'pos': pos, 'speed': speed}
      _lock.release()
    
      time.sleep(max(0, next-time.time()))
      next += t


class BBSimPosixQueue(BBSimActivityBase):
  """ A ball and beam class using Posix message queues """
  def __init__(self, id):
    BBSimActivityBase.__init__(self, id)

  def setup_communication(self):
    self.qout1 = ipc.MessageQueue("/bbsim_out1-{}".format(bb.id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
    self.qout2 = ipc.MessageQueue("/bbsim_out2-{}".format(bb.id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
    self.qin = ipc.MessageQueue("/bbsim_in-{}".format(bb.id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
    self.qreset = ipc.MessageQueue("/bbsim_reset-{}".format(bb.id), flags=ipc.O_CREAT, mode=0666, max_messages=1)
    # Provides the possibility to read the state perfectly
    self.x2 = ipc.MessageQueue("/bbsim_ballspeed-{}".format(bb.id), flags=ipc.O_CREAT, mode=0666, max_messages=1)

  def read_input(self):
    try:
      message, priority = self.qin.receive(0) # Get input signal
      self.u = float(message)
    except ipc.BusyError:
      pass
    return self.u

  def write_output(self, position, angle, _ball_speed):
    try: self.qout1.receive(0) # Queue is of size one, clear pending message
    except ipc.BusyError: pass
    try: self.qout2.receive(0) # Queue is of size one, clear pending message
    except ipc.BusyError: pass
    try: self.x2.receive(0) # Queue is of size one, clear pending message
    except ipc.BusyError: pass
  
    self.qout1.send("{}".format(angle), timeout=0) # Write message, queue is guranteed to be empty
    self.qout2.send("{}".format(position), timeout=0) # Write message, queue is guranteed to be empty
    self.x2.send("{}".format(_ball_speed), timeout=0) # Write message, queue is guranteed to be empty

  def is_reset(self):
    reset = True
    try: 
      self.qreset.receive(0) # If there is a message then reset
    except ipc.BusyError: reset = False
    return reset

class BBSimPosixShm(BBSimActivityBase):
  """ A ball and beam class using Posix shared memory message queues """
  def __init__(self, id):
    BBSimActivityBase.__init__(self, id)
    os.remove("/dev/shm/sem.bbsim_shm_lock-{}".format(id))
    self.lock = ipc.Semaphore("/bbsim_shm_lock-{}".format(id), flags=ipc.O_CREAT, mode=0666, initial_value=1)
    self.shm = ipc.SharedMemory("/bbsim_shm-{}".format(id), flags=ipc.O_CREAT, mode=0666, size=1024)
    self.mm = MemMapped(self.shm.fd, self.lock)

  def read_input(self):
    self.mm.lock()
    val = self.mm.read_float(0)
    self.mm.unlock()
    return val

  def write_output(self, position, angle, _ball_speed=0):
    self.mm.lock()
    self.mm.write_float(angle, 8)
    self.mm.write_float(position, 16)
    self.mm.write_float(_ball_speed, 24)
    self.mm.unlock()

  def is_reset(self):
    self.mm.lock()
    reset = self.mm.read_byte(32)
    if reset == 1:
      self.mm.write_float(0, 0)
      self.mm.write_float(0, 8)
      self.mm.write_float(0, 16)
      self.mm.write_float(0, 24)
      self.mm.write_byte(0, 32)
    self.mm.unlock()
    return reset


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

def thread_main(bb, h):
  bb.setup_communication()
  bb.run(BBSim(coulombFrictionFactor=0.01), h, bb.id)

def slurpfile(path):
  with open(path, 'r') as f:
    contents=f.read()
  return contents


if __name__ == "__main__":
  global _sigint
  description=slurpfile('about.txt')
  parser = argparse.ArgumentParser(description=slurpfile('about.txt'), formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-c', '--plants', type=int, default=1,
                  help='Number of ball and beam plants')
  parser.add_argument('-t', '--period', type=int, default=10,
                    help='Update interval in milliseconds (default 10 ms)')
  parser.add_argument('--ipc', type=str, default='shm',
                    help='IPC method: shm or queue. Default: shm')

  args = parser.parse_args()

  _sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, sig_int_handler)

  os.umask(0)
  _lock = threading.Lock()
  _state = []
  for x in range(0, args.plants):
    _state.append({'angle': 0, 'pos': 0, 'speed': 0})
  for x in range(0, args.plants):
    if args.ipc == 'shm':
      bb = BBSimPosixShm(x)
    else:
      bb = BBSimPosixQueue(x)
    th = threading.Thread(target=thread_main, args=(bb, float(args.period)/1000.0))
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
