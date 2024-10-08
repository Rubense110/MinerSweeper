from abc import abstractmethod
from pm4py.objects.petri_net.obj import PetriNet
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

class Metrics():

    def __init__(self: PetriNet):
        self.n_of_metrics = 0
        self.metrics_array = np.array([])
        self.labels = []

    @abstractmethod
    def get_n_of_metrics(self):
        pass

    @abstractmethod
    def get_metrics_array(self):
        pass

    @abstractmethod
    def get_labels(self):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

class BasicMetrics(Metrics):

    def __init__(self):
        super(Metrics, self).__init__()

        n_places = 0
        n_arcs = 0
        n_transitions = 0
        cycl_complx = 0
        ratio = 0
        joins = 0
        splits = 0

        
        self.metrics_array = np.array([n_places, n_arcs, n_transitions, cycl_complx, ratio, joins, splits])
        self.n_of_metrics = len(self.metrics_array)
        self.labels = ['n_places', 'n_arcs', 'n_transitions', 'cycl_complx', 'ratio', 'joins', 'splits']

    def get_metrics_array(self, petri: PetriNet):

        # basic metrics
        n_places = len(petri.places)
        n_transitions = len(petri.transitions)
        n_arcs = len(petri.arcs)

        # Cyclomatic complexity
        cycl_complx = n_arcs - (n_places + n_transitions) + 2

        #ratio states/transition
        ratio = n_places/n_transitions

        #joins & splits
        joins, splits = self._get_joins_splits(petri.arcs)

        # -joins & -splits if Maximize, joins & splits if Minimize
        self.metrics_array = np.array([n_places, n_arcs,
                                       n_transitions, cycl_complx, 
                                       ratio, joins, splits])
        return self.metrics_array
    
    def get_n_of_metrics(self):
        return self.n_of_metrics
    
    def get_labels(self):
        return self.labels
    
    def __str__(self) -> str:
        return 'basic'
    
    def _get_joins_splits(self,arcs):

        splits = dict()
        joins = dict()
        n_splits = 0
        n_joins = 0

        for arc in arcs:

            if arc.source not in splits:
                splits[arc.source] = [arc.target]
            else:
                splits[arc.source].append(arc.target)

            if arc.target not in joins:
                joins[arc.target] = [arc.source]
            else:
                joins[arc.target].append(arc.source)

        for i in splits.values():
            if len(i) > 1: n_splits+=1

        for i in joins.values():
            if len(i) > 1: n_joins+=1

        return (n_splits, n_joins)

class BasicMetricsUsefullSimple(BasicMetrics):

    ## RULES
    NSFE_TRESHOLD_MORE_THAN = 1.5
    NSFE_TRESHOLD_LESS_THAN = 0.5
    GM_TRESHOLD_MORE_THAN = 1.5
    
    def __init__(self):
        super().__init__()
        
    def get_metrics_array(self, petri: PetriNet):
        petri_graph = self.__convert_petri_to_graph(petri)

        NSFE = self.__calculate_nsfe(petri)
        IS_AP = nx.is_aperiodic(petri_graph)
        GM = self.__calculate_gm(petri)

        if  IS_AP or  self.__check_nsfe_interval(NSFE) or  self.__check_gm_interval(GM):
            return super().get_metrics_array(petri)
        else:
            penalty = 1e6
            return np.array([penalty] * self.n_of_metrics)
            

    def __check_nsfe_interval(self, NSFE):
        if NSFE <= self.NSFE_TRESHOLD_LESS_THAN or NSFE > self.NSFE_TRESHOLD_MORE_THAN:
            return True
        else:
            return False
    def __check_gm_interval(self, GM):
        if GM > self.GM_TRESHOLD_MORE_THAN:
            return True
        else:
            return False
    
    def __convert_petri_to_graph(self, petri: PetriNet):
        graph = nx.DiGraph()

        for place in petri.places:
            graph.add_node(place, type= "place")

        for transition in petri.transitions:
            graph.add_node(transition, type= "transition")

        for arc in petri.arcs:
            graph.add_edge(arc.source, arc.target)

        return graph
    
    def __calculate_gm(self, petri: PetriNet):
        '''Overall difference between incoming and outgoing'''
        gm = 0
        for place in petri.places:
            in_count = len(place.in_arcs)
            out_count = len(place.out_arcs)
            gm += abs(in_count - out_count)
        gm = gm//len(petri.places)
        return gm

    def __calculate_nsfe(self, petri: PetriNet):
        '''Total number of outgoing flows from events'''
        nsfe = 0
        for places in petri.places:
            nsfe += len(places.out_arcs)
        nsfe = nsfe/len(petri.places) # Normalize
        return nsfe

    def __str__(self) -> str:
        return 'basic_useful'
    
## TESTING
if __name__ == "__main__":

    from pm4py.objects.log.importer.xes import importer as xes_importer
    from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
    from pm4py.visualization.petri_net import visualizer as pn_visualizer



    log = xes_importer.apply('test/Closed/BPI_Challenge_2013_closed_problems.xes')
    net, initial_marking, final_marking = heuristics_miner.apply(log)

    gviz = pn_visualizer.apply(net, initial_marking, final_marking)
    pn_visualizer.view(gviz)

    metrics_obj =  BasicMetricsUsefullSimple()
    metrics_labels = metrics_obj.get_labels()
    print(metrics_obj.get_metrics_array(net))

    def show(metrics):
        print(type(metrics), metrics)
        print("\n### METRICS ###")
        print(f"{metrics_labels[0]}:    {metrics[0]}")
        print(f"{metrics_labels[1]}:    {metrics[1]}")
        print(f"{metrics_labels[2]}:    {metrics[2]}")
        print(f"{metrics_labels[3]}:    {metrics[3]}")
        print(f"{metrics_labels[4]}:    {metrics[4]}")
        print(f"{metrics_labels[5]}:    {metrics[5]}")
        print(f"{metrics_labels[6]}:    {metrics[6]}\n")
        print(f"Nº of metrics: {metrics_obj.get_n_of_metrics()}")
