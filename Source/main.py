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
        a = ["spring", "damper", "inerter"]
        return f"{a[self.degree]} of constant {self.value}"

class Node:
    def __init__(self, mass, x, element_coordinate_pair, excitation):
        self.excitation = excitation
        self.mass = mass
        self.x = x
        self.element_coordinate = element_coordinate_pair
        self.elements = element_coordinate_pair[:][0]
        self.coordinates = element_coordinate_pair[:][1]
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
        lhs = self.excitation
        rhs = self.mass*self.x + sum([
            element.value*(self.x*self.s**element.degree - coordinate*self.s**element.degree) for element, coordinate in self.element_coordinate
        ])
        return rhs, lhs
    

class Network:
    def __init__(self, topology, masses, excitation):
        self.updated_df = False
        self.excitation = excitation
        self.topology = topology
        self.arr_topology = np.array(list(self.topology.values()))
        
        self.masses = self.reorder_masses(masses)
        self.coordinates = self.generate_coordinate()

        self.asdf_topology = self.df_topology()

        self.elements = self.generate_elements()
        self.update_asdf()
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
        objects = [Element(i,j) for (i,j) in zip(self.asdf_topology.value, self.asdf_topology.deg)]
        return {
            key:value for (key,value) in zip(variables, objects)
        }

    def reorder_masses(self, masses):
        return dict(sorted(masses.items()))

    def generate_coordinate(self):
        coordinates = set()
        for i in self.arr_topology[:,2]:
            coordinates = coordinates | i
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
            x = self.coordinates[f"x{i+1}"]
            mass = list(self.masses.values())[i]
            ops = self.excitation if i==0 else 0

            temp =  self.asdf_topology[["Element", "first coordinate", "second coordinate"]]
            mask1 = temp["first coordinate"]  == str(x)
            mask2 = temp["second coordinate"] == str(x)
            A = (temp["second coordinate"]*mask1)*(not mask2.all())
            B = (temp["first coordinate"]*(not mask1.all()))*mask2

            element_coord = pd.concat([temp["Element"], A+B], axis=1)
            element_coord.columns = ["Elements", "Coordinate"]
            element_coord = element_coord.drop(element_coord[element_coord['Coordinate'] == ''].index)
            element_coord["Coordinate"] = [self.coordinates[i] for i in element_coord["Coordinate"]]
            element_coord_tuples = [tuple(element_coord.iloc[i, [0, 1]]) for i in range(element_coord.shape[0])]
            
            nodes.append(Node(mass, x, element_coord_tuples, ops))

        return nodes

    def df_topology(self):
        a = np.array([list(i) for i in self.arr_topology[:,2]])
        #a = np.array([[self.coordinates[j] for j in i] for i in self.arr_topology[:,2]])

        return pd.DataFrame({
            "Element"            : self.topology.keys(),
            "deg"                : self.arr_topology[:,0],
            "value"              : self.arr_topology[:,1],
            "first coordinate"   : a[:,0],
            "second coordinate"  : a[:,1],
        })

    def transfer(self):
        eqs = np.array([i.eom() for i in self.nodes])
        RHS, LHS = self.matricize(eqs[:,:-1], eqs[:,-1])
        solution = sym.linsolve((RHS, LHS), list(self.coordinates.values())).args[0]
        return solution[-1]/solution[0]

    def matricize(self, rhs, lhs):#switching rhs and lhs
        RHS = sym.Matrix(
            [ [i[0].coeff(j) for j in self.coordinates.keys()] for i in rhs ]
        )
        LHS = sym.Matrix(
            [[i] for i in [self.excitation]+[0]*(len(self.coordinates)-1)]
        )
        return RHS, LHS
    
    def update_asdf(self):
        if (not self.updated_df):
            #This may not be optimized
            self.asdf_topology["Element"] = [self.elements[sym.Symbol(i)] for i in self.asdf_topology["Element"]]
        self.updated_df = True
    
def is_float(input):
    try:
        float(input)
        return True
    except Exception as e:
        print(e)
        return False