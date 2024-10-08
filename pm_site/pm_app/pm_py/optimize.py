from . import metrics 
from . import parameters 
from . import utils 
from . import problem

from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from jmetal.algorithm.multiobjective.nsgaii import NSGAII


class Optimizer(problem.PM_miner_problem):
    '''
    This class performs hyperparameter optimization of process mining algorithms using different techniques implemented
    on the Jmetal metaheuristic algorithm optimization framework

    This class manages the main optimization process, storing the results and extracting the pareto front approximation,
    it also provides methods to retrieve solutions, visualize them, and convert them to petri nets.

    The class extends the pm_miner_problem class, wich specifies the optimization problem, including how solutions are created and evaluated.

    Attributes
    ----------
    miner : class
        The mining algorithm class being optimized (e.g., heuristics_miner, inductive_miner).
    log : object
        The loaded event log data.
    metrics_obj : object
        The type of metrics used for evaluation. Must be one of te implementations from the 'metrics' module
    
    '''

    def __init__(self, miner, log, metrics_obj):
        parameters_info = self.__get_parameters(miner, log)
        super().__init__(miner, log, metrics_obj, parameters_info)
    
    def __get_parameters(self, miner, log):
        '''
        Returns the hiperparameters to be optimized, as each miner has its own hiperparameters each one requires a different approach.

        Parameters
        ----------
        miner : class
            The mining algorithm class for which to retrieve hyperparameters (e.g., heuristics_miner, inductive_miner).
        log : object
            The loaded event log data.

        Returns
        -------
        parameters.BaseParametersConfig : An instance of the hyperparameters class corresponding to the specified miner.

        '''
        if miner == heuristics_miner:
            params = parameters.HeuristicParametersConfig(log)
            return params
        elif miner == inductive_miner:
            params = parameters.InductiveParametersConfig()
            return params
        else:
            raise ValueError(f"Miner '{miner}' not supported. Available miners are: heuristic, inductive")

    def show_result(self):
        '''
        Displays the solutions obtained by the algorithm in the console.
        '''

        print("\n### RESULT ###\n")
        for (i,j)in enumerate(self.result):
            print("Solution ",i," :")
            print("     variables: ",j.variables)
            print("     objectives:",j.objectives.tolist(),"\n")
        print("##############")

    def discover(self,algorithm_class, **params):
        '''
        Executes hyperparameter optimization using the specified algorithm.

        This method initializes and runs the optimization process using a given Jmetal algorithm class. 
        The algorithm is executed with the specified hyperparameters, and the method stores the results, including 
        the final solutions and non-dominated solutions (Pareto front).

        Parameters
        ----------
        algorithm_class : class
            The class of the optimization algorithm to be used. This class must be from the Jmetal optimization framework.
        **params : dict, optional
            Additional keyword arguments representing the hyperparameters to be passed to the algorithm class.
        '''
        self.algorithm = algorithm_class(problem=self, **params)
        self.algorithm.run()
        self.result = self.algorithm.result()
        self.non_dom_sols = utils.calculate_pareto_front(self.result)


    def get_result(self):
        '''
        Returns
        -------
        List[FloatSolutions] : A list contaning all Solutions generated by the algorithm in the last iteration.
        '''
        return self.result
        
    def get_best_solution(self):
        '''
        Returns
        -------
        FloatSolution : The best solution found by the algorithm
        '''
        return self.get_non_dominated_sols()[0]  # TO-DO

    def get_petri_net(self, sol=None):
        '''
        Parameters
        ----------
        sol : FloatSolution
            The solution to be converted to petri net. 

        Returns
        -------
        Tuple(net, initial marking, final marking) : A tuple contaning the petri net and the initial and final marking
                                                     for the specified solution, or the best solution if none is specified.
        '''
        if sol is None:
            sol = self.get_best_solution()

        params = {key: sol.variables[idx] for idx, key in enumerate(self.parameters_info.param_range.keys())}

        petri_net, initial_marking, final_marking = self._create_petri_net_sol(params)
        return petri_net, initial_marking, final_marking
    
    def get_non_dominated_sols(self):
        '''
        Returns
        -------
        List[FloatSolution] :  A list contaning the non-dominated solutions found by the algorithm
        '''
        return self.non_dom_sols
    
    def plot_pareto_front(self, title, filename):
        '''
        Plots the pareto front aproximation based on the algorithm's results.

        This method plots and saves the front in the specified file

        Parameters
        ----------
        title : str
            The title of the plot.
        filename : str
            The path of the file where the plot will be saved.
        '''
        utils.plot_pareto_front(self.result,
                                axis_labels=self.metrics_obj.get_labels(),
                                title = title,
                                filename=filename)


    def get_pareto_front_petri_nets(self):
        '''
        Returns
        -------
        List[Tuple(net, initial marking, final marking)] :  A list containing the petri nets of all solutions from 
                                                            the pareto front approximation.
        '''
        front = self.get_non_dominated_sols()
        petri_nets_from_pareto_sols = list()
        for sol in front:
            petri_nets_from_pareto_sols.append(self.get_petri_net(sol))
        return petri_nets_from_pareto_sols

    
## Testing

if __name__ == "__main__":

    from pm4py.objects.log.importer.xes import importer as xes_importer
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    from jmetal.operator.crossover import SBXCrossover
    from jmetal.operator.mutation import PolynomialMutation
    from jmetal.util.termination_criterion import StoppingByEvaluations


    max_evaluations = 1000

    log = xes_importer.apply('event_logs/Closed/BPI_Challenge_2013_closed_problems.xes')
    metrics_obj = metrics.Basic_Metrics()

    opt = Optimizer(heuristics_miner, log, metrics_obj)

    nsgaii_params = {'population_size': 100,
                     'offspring_population_size': 100,
                     'mutation': PolynomialMutation(probability=1.0 / opt.number_of_variables, distribution_index=20),
                     'crossover': SBXCrossover(probability=1.0, distribution_index=20),
                     'termination_criterion': StoppingByEvaluations(max_evaluations=max_evaluations)}
    
    opt.discover(algorithm_class=NSGAII, **nsgaii_params)
    
    optimal_petri_net, initial_marking, final_marking = opt.get_petri_net()

    # visualize petri net
    gviz = pn_visualizer.apply(optimal_petri_net, initial_marking, final_marking)
    pn_visualizer.view(gviz)

    # plot Pareto front
    opt.plot_pareto_front(title='Pareto front approximation', filename='NSGAII-Pareto-Closed')