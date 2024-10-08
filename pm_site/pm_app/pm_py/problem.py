from . import metrics
from . import parameters

import random
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.convert import convert_to_petri_net
from jmetal.core.problem import FloatProblem, FloatSolution


class PM_miner_problem(FloatProblem):
    '''
    Custom optimization problem for process mining. The goal of this problem class is to
    tune the hiperparameters of the chosen process mining algorithm in order to find useful
    process models, measuring them following the specified metrics.

    This class extends 'FloatProblem' from the Jmetal metaheuristic optimization framework..

    Attributes
    ----------
    miner : pm4py.miner
        The selected process mining algorithm (e.g., Heuristic Miner, Inductive Miner).
    log : object
        The event log loaded using pm4py (in XES format).
    metrics_obj : Metrics
        An object that defines how to calculate the fitness of a mined process model. 
        Must be one implementation from the 'metrics' module.
    parameters_info : parameters.BaseParameters
        Contains relevant information about the hiperparameters of the chosen miner such as
        their value range and data type.


    '''

    def __init__(self, miner, log, metrics_obj: metrics.Metrics, parameters_info: parameters.BaseParametersConfig):
        
        super(PM_miner_problem, self).__init__()

        self.miner = miner                       # pm4py miner e.g. heuristic_miner
        self.log = log                           # XES log (already loaded by pm4py)
        self.metrics_obj = metrics_obj           # How to calculate fitness
        self.parameters_info = parameters_info   # Miner pararameters (selected automatically)

        self.n_of_objectives = metrics_obj.get_n_of_metrics()
        self.number_of_variables = self.__get_n_genes()
        self.number_of_constraints = 0

        self.lower_bound, self.upper_bound = self.__get_bounds()
        self.obj_labels = metrics_obj.get_labels()

    def __get_bounds(self): 
        '''
        Determines the value range for the parameters of the specified miner
        '''
        lower_bound = [i[0] for i in self.parameters_info.param_range.values()]
        upper_bound = [i[1] for i in self.parameters_info.param_range.values()]
        return lower_bound, upper_bound
    
    def __get_n_genes(self):
        '''
        range of posible values for each gene (miner parameter)
        '''
        return len(self.parameters_info.param_range)
        
    def evaluate(self, solution: FloatSolution) -> FloatSolution :
        '''
        Specifies ho solutions will be evaluated.It generates the petri net corresponding to the solution 
        and then uses the specified metrics to evaluate it.
        '''
        params = {key: solution.variables[idx] for idx, key in enumerate(self.parameters_info.param_range.keys())}
        petri, _, _ = self._create_petri_net_sol(params)
        solution.objectives = self.metrics_obj.get_metrics_array(petri)
        solution.n_of_objectives = self.n_of_objectives
        
        return solution
    
    def _create_petri_net_sol(self, params):
        '''
        Auxiliary function to manage the petri net generation, as its particularities depend of the selected miner.
        Currently only inductive and heuristic miners are suported.
        '''
        if self.miner == heuristics_miner:
            petri, initial_marking, final_marking = self.miner.apply(self.log, parameters= params)
        elif self.miner == inductive_miner:
            inductive_variant = inductive_miner.Variants.IMf if params["noise_threshold"] > 0 else inductive_miner.Variants.IM
            params["multi_processing"] = True if params["multi_processing"] > 0.5 else False
            params["disable_fallthroughs"] = True if params["disable_fallthroughs"] > 0.5 else False
            process_tree = self.miner.apply(self.log, variant = inductive_variant,  parameters= params )
            petri, initial_marking, final_marking = convert_to_petri_net(process_tree)    
        return petri, initial_marking, final_marking
    
    def create_solution(self) -> FloatSolution:
        '''
        Specifies how solutions are created, the actual process depends of the parameter type specified
        in the parameters module.
        '''
        new_solution = FloatSolution(number_of_constraints=self.number_of_constraints,
                                     number_of_objectives=self.n_of_objectives,
                                     lower_bound = self.lower_bound,
                                     upper_bound = self.upper_bound)   
        # Random Solution
        random_sol = list()
        for index, param_and_type in enumerate(self.parameters_info.param_type.items()):
            data_type = param_and_type[1]
            if data_type == int: 
                random_sol.append(random.randint(self.lower_bound[index], self.upper_bound[index]))
            elif data_type == bool:
                random_sol.append(random.choice([True, False]))
            else:
                random_sol.append(random.uniform(self.lower_bound[index], self.upper_bound[index]))


        new_solution.variables = random_sol
        return new_solution

    def name(self) -> str:
        return 'Custom Process Mining Problem'
    
    def number_of_constraints(self) -> int:
        return self.number_of_constraints
    
    def number_of_variables(self) -> int:
        return self.number_of_variables
    
    def number_of_objectives(self) -> int:
        return self.n_of_objectives