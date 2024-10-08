from jmetal.operator.crossover import *
from jmetal.operator.mutation import *
from jmetal.util.termination_criterion import *

mutations = {
      'polynomial'  : PolynomialMutation,
      'random'      : SimpleRandomMutation,
      'uniform'     : UniformMutation,
      'non_uniform' : NonUniformMutation,
}

crossovers = {
      'pmx'     : PMXCrossover,
      'sbx'     : SBXCrossover,
}

def get_hipparam_dict(form_data):
        
        param_dict = {}
        optimization_method = form_data['optimization_method']

        mutation_type = form_data['mutation_type']
        mutation_probability = form_data['mutation_probability']
        crossover_type = form_data['crossover_type']
        crossover_probability = form_data['crossover_probability']
        max_evaluations = form_data['max_evaluations']

        param_dict['population_size'] = form_data['population_size']
        if optimization_method != 'NSGAIII':
            param_dict['offspring_population_size'] = form_data['offspring_population_size']
        param_dict['mutation'] = mutations[mutation_type](mutation_probability)
        param_dict['crossover'] = crossovers[crossover_type](crossover_probability)
        param_dict['termination_criterion'] = StoppingByEvaluations(max_evaluations=max_evaluations)

        return param_dict
