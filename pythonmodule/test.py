#!/usr/bin/env python

import cotc.sim.ballnbeam as bbsim

import cotc.qpgen as mpclib
bb = mpclib.load_mpc('ballnbeam', 30)
bb.init()
print(bb.get_horizon_max())


