#!/usr/bin/env python

import argparse
import socket
import struct

import math
import matplotlib.pyplot as plt
import numpy as np
import time
import collections

parser = argparse.ArgumentParser(description='Plot UDP input')
parser.add_argument('-t', '--title', default="UDP Plot", metavar='string',
									help='Sets a title to the figure')
parser.add_argument('-a', '--address', default='localhost', metavar='ipv4-address',
                  help='Address to bind to (default: localhost)')
parser.add_argument('-p', '--port', type=int, default=51001, metavar='number',
                help='Port to listen to (default 51001)')
parser.add_argument('-l', '--limits', type=float, nargs='+', metavar='number',
                help='Set plot limits')
parser.add_argument('-i', '--interval', type=float, default=0.0625, metavar='seconds',
                help='Update interval')
parser.add_argument('-s', '--select', type=int, nargs='+', default=None, metavar='indexes',
                help='Select only some signals')
parser.add_argument('-g', '--graphlen', type=float, default=60, metavar='seconds',
							help='Number of seconds to show in graph')
parser.add_argument('names', metavar='N', nargs='+', help="Names of variables to plot")
args = parser.parse_args()

h = args.interval
numvars = len(args.names)

if args.select == None:
	select = range(0, numvars)
else:
	select = args.select

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((args.address, int(args.port)))

rows=cols=round(math.sqrt(numvars))
if rows*cols < numvars:
  rows += 1
fig = plt.figure(figsize=(8,6))
fig.canvas.set_window_title(args.title)

# some X and Y data
numdatapoints=int(math.ceil(args.graphlen/h));
x = np.arange(numdatapoints)*h
y = [None] * numvars
li = [None] * numvars
ax = [None] * numvars
for i in range(0, numvars):
  y[i] = collections.deque([0]*numdatapoints, maxlen=numdatapoints)
  ax[i] = fig.add_subplot(rows*100+cols*10+i+1)
  ax[i].set_title(args.names[i])
  li[i], = ax[i].plot(x, y[i])
  if args.limits and len(args.limits) >= i+1:
    ax[i].set_ylim([-args.limits[i], args.limits[i]])
  else:
    ax[i].relim()
    ax[i].autoscale_view(True,True,True)
    

# draw and show it
fig.canvas.draw()
plt.show(block=False)

sock.setblocking(0)
nexttime = time.time()+h
while True:

  newdata = None
  while True:
    try:
      data, addr = sock.recvfrom(1024)
      newdata = data
    except: break

  if newdata:
		# All data is expected to be 32 bit double
    var = struct.unpack('!{}d'.format(len(newdata)/8), newdata)
    for i in range(0, numvars):
      y[i].append(var[select[i]])
  else:
    for i in range(0, numvars):
      y[i].append(y[i][-1])

  try:
    for i in range(0, numvars):
      li[i].set_ydata(y[i])
      ax[i].relim()
    fig.canvas.draw()
  except KeyboardInterrupt:
    break

  d = nexttime-time.time()
  if d > 0:
    time.sleep(d)
  nexttime += h

