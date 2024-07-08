import numpy as np  # type: ignore
import sympy as sym # type: ignore
import pandas as pd # type: ignore

"""
Takes in a network represented by its nodes
"""

class Element:
    def __init__(self, value, degree):
        self.value = value
        self.degree = degree

    def __str__(self) -> str:
        return """
            Represents element objects such as springs dampers and inerters.
            """

class Node:
    def __init__(self, mass, x, element_coordinate_pair, excitation):
        self.excitation = excitation
        self.mass = mass
        self.x = x
        self.element_coordinate = element_coordinate_pair
        self.elements = element_coordinate_pair[:,0]
        self.coordinates = element_coordinate_pair[:,1]
        self.s = sym.Symbol("s")

    def __str__(self) -> str:
        return """
            Creates a node with a mass, and associated coordinate relations

            The relation is dictated by the element and the coordinate. The
            coordinate must be a symbolic variable
            """
    
    def eom(self):
        """
        Automatically returns the L.T. of the equation of motion
        """
        rhs = self.excitation
        lhs = self.mass*self.x + sum([
            element.value*(self.x*self.s**element.deg - coordinate*self.s**element.deg) for element, coordinate in self.element_coordinate
        ])
        return rhs, lhs
    

class Network:
    def __init__(self, topology, masses, excitation):
        self.excitation = excitation

        self.topology = topology
        self.arr_topology = np.array(list(self.topology.values()))
        self.asdf_topology = self.df_topology()

        self.masses = self.reorder_masses(masses)
        self.coordinates = self.generate_coordinate()
        self.elements = self.generate_elements()
        self.nodes = self.generate_nodes()


    def __str__(self) -> str:
        return """
            Code takes dictionaries of masses and elements, the element dictionnary represents the topology of the network. Inputs should look like this for example:

            #Example
            k1, b, k3, c, k2, k4 = 10, 300, 20, 15, 50, 12

            network = {
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
               """
    
    def generate_elements(self):
        variables = [sym.Symbol(i) for i in self.topology.keys()]
        objects = [Element(i,j) for [i,j] in self.topology[:][1,0]]
        return {
            key:value for (key,value) in zip(variables, objects)
        }

    def reorder_masses(self, masses):
        return dict(sorted(masses.items()))

    def generate_coordinate(self):
        coordinates = set()
        for i in self.arr_topology[:,2]:
            coordinates = self.coordinates | i
        assert len(coordinates) == len(self.masses), "There should be one coordinate per mass element"

        return {i:sym.Symbol(i) for i in sorted(coordinates)}

    def get(self, request):
        try:
            return self.objects[request]
        except KeyError:
            return f"Please, choose one of the following as a requested objects {self.objects.keys}"
        except Exception as e:
            return e

    def generate_nodes(self):
        nodes = []

        for i in range(len(self.coordinates)):
            x = self.coordinates[i]
            mass = list(self.masses.values())[i]
            ops = self.excitation if i==0 else 0

            temp =  self.asdf_topology.loc[
                    (self.asdf_topology["first coordinate"] == x) or \
                        (self.asdf_topology["second coordinate"] == x),
                    "Element", "first coordinate", "second coordinate"]
            mask1 = temp["first coordinate"]  == x
            mask2 = temp["second coordinate"] == x
            element_coord = pd.concat([temp["Element"], temp["first coordinate"]*mask1 + temp["second coordinate"]*mask2], axis=1)
            
            nodes.append(Node(mass, x, element_coord.itertuples(index=False, name=False), ops))
        
        return nodes

    def df_topology(self):
        return pd.DataFrame({
            "Element"            : self.topology.keys(),
            "deg"                : self.arr_topology[:,0],
            "value"              : self.arr_topology[:,1],
            "first coordinate"   : self.coordinates[sorted(self.arr_topology[:,2])[0]],
            "second coordinate"  : self.coordinates[sorted(self.arr_topology[:,2])[2]],
        })

    def transfer(self):
        eqs = np.array([i.eom for i in self.nodes])
        RHS, LHS = self.matricize(eqs[:,0], eqs[:,1])
        solution = np.linalg.solve(RHS, LHS)
        return solution[-1]/solution[0]

    def matricize(self, rhs, lhs):
        RHS = np.array(
            [ [i.coeff(j) for j in self.coordinates.keys()] for i in rhs ]
        )
        LHS = np.array(
            [[i] for i in [self.excitation]+[0]*(len(self.coordinates)-1)]
        )
        return RHS, LHS