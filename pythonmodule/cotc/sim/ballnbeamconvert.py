import math
def v2out(x): return int((x/10.0+1)*2048)
def in2v(x): return (x-32767)/3276.7
def v2angle(x): return (x/10.0)*(math.pi/4)
def angle2v(x): return (x/(math.pi/4))*10
def angle2deg(x): return (180/math.pi)*x
def in2angle(x): return v2angle(in2v(x))
def v2position(x): return (x/10.0)*0.55
def position2v(x): return (x/0.55)*10.0
def v2angular(x): return (x/10.0)*4.4
def angular2v(x): return (10*x)/4.4
def in2position(x): v2position(in2v(x))
