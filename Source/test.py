from main import *

k1, b, k3, c, k2, k4 = 10, 300, 20, 15, 50, 12

topology = {
"k1"    : (0, k1, {"x1", "x4"}),
"b"     : (2, b, {"x1", "x2"}),
"k3"    : (0, k3, {"x2", "x3"}),
"c"     : (1, c, {"x2", "x3"}),
"k2"    : (0, k2, {"x3", "x4"}),
"k4"    : (1, k4, {"x1", "x2"}),
}

masses = {
"m1"    : 5,
"m2"    : 5,
"m3"    : 5,
"m4"    : 5,
}

MyNetwork = Network(topology=topology, masses=masses, excitation=sym.Symbol("s"))
print(MyNetwork.transfer())