from main import *

if __name__ == "__main__":

    running = True
    while running:

        action = input("Choose an action\n")

        if action == "quit":
            running = False

        elif action == "network":
            masses = dict()
            i = 1
            temp = input(f"m{i}: ")

            while is_float(temp):
                masses[f"m{i}"] = temp
                i += 1
                temp = input(f"m{i}: ")
            print(f"Here are your entered masses: {masses}")

            print("Now you will define your network topology")
            topology = dict()
            element_counts = [0]*3 #spring, damper, inerter
            running = True
            
            while running:
                element_type = ["spring", "damper", "inerter"].index(input("choose between spring, damper, or interter: "))
                element_counts[element_type] += 1
                element_value = int(input("Value: "))
                connected_masses = [int(i) for i in input("Connected to which masses? Enter as 1, 2 if you mean mass 1 and 2\n").split(",")]
                idx = ["k","b","c"][element_type] + str(element_counts[element_type])
                topology[idx] = (
                    element_type, 
                    element_value, 
                    set([f"x{connected_masses[0]-1}", f"x{connected_masses[1]-1}"])
                )
                running = bool(input("Add an element to your topology? Answer by either 1 or 0.\n"))
            
            excitation = sym.parsing.sympy_parser.parse_expr(input("Enter your excitation function:\n"))
            MyNetwork = Network(topology, masses, excitation)
        
        elif action == "transfer":
            try:
                MyNetwork.transfer()
            except Exception as e:
                print(e)

    quit()