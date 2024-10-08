crossovers = {
    'jmetal.operator.crossover.PMXCrossover' : 'pmx',
    'jmetal.operator.crossover.SBXCrossover' : 'sbx',
}

mutations = {
    'jmetal.operator.mutation.PolynomialMutation' : 'polynomial',
    'jmetal.operator.mutation.SimpleRandomMutation' : 'random',
    'jmetal.operator.mutation.UniformMutation' : 'uniform',
    'jmetal.operator.mutation.NonUniformMutation' : 'non_uniform',
}

def import_from_json(json_data):

    execution_name = json_data['execution']['name']
    event_log = json_data['execution']['path_events_log']
    metrics = json_data['execution']['metrics']
    miner = json_data['execution']['miner']
    optimizer = json_data['optimizer']['name']
    population_size = json_data['optimizer']['hip_params']['population_size']
    off_population_size = None
    if optimizer != 'NSGAIII':
        off_population_size = json_data['optimizer']['hip_params']['offspring_population_size']

    mutation_type = mutations[json_data['optimizer']['hip_params']['mutation'][0]]
    mutation_prob = json_data['optimizer']['hip_params']['mutation'][1]['probability']

    crossover_type = crossovers[json_data['optimizer']['hip_params']['crossover'][0]]
    crossover_prob = json_data['optimizer']['hip_params']['crossover'][1]['probability']

    max_evaluations = json_data['optimizer']['hip_params']['termination_criterion'][1]['max_evaluations']

    POST_form_data = {
        'execution_name': execution_name,
        'event_log': event_log,
        'evaluation_metrics': metrics,
        'miner_type': miner,
        'optimization_method': optimizer,
        'population_size': population_size,
        'mutation_type': mutation_type,
        'mutation_probability': mutation_prob,
        'crossover_type': crossover_type,
        'crossover_probability': crossover_prob,
        'max_evaluations': max_evaluations,
    }

    if off_population_size: 
        POST_form_data['offspring_population_size'] = off_population_size

    return POST_form_data
