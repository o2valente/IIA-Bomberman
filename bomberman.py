#
# Modulo: cidades
# 
# Implementacao de um dominio para planeamento de caminhos
# entre cidades usando para esse efeito o modulo tree_search
#
# (c) Luis Seabra Lopes, Introducao a Inteligencia Artificial, 2012/2013
#


from tree_search import *

class bomberman(SearchDomain):
    def __init__(self,connections, coordinates):
        self.connections = connections
        self.coordinates = coordinates
    def actions(self,path):                 # Verificar se é preciso.
        actlist = []
        for (P1,P2,D) in self.connections:
            if (P1==path):
                actlist += [(P1,P2)]
            elif (P2==path):
               actlist += [(P2,P1)]
        return actlist 
    def result(self,path,action):
        (P1,P2) = action
        if P1==path:
            return P2
    def cost(self, path, action):
        (P1,P2) = action
        if P1 != path:
            return None == (p1,p2)
        for(p1,p2,D) in self.connections:
            if action == (p1,p2) or action == (p2,p1):
                return D;
        pass
    def heuristic(self, state, goal_state):
        pass


# Atalho para obter caminho de c1 para c2 usando strategy:
def search_path(domain,P1,p2,strategy):
    my_prob = SearchProblem(domain,p1,p2)
    my_tree = SearchTree(my_prob)
    my_tree.strategy = strategy
    return my_tree.search()