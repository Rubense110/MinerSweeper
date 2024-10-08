import os
from time import time
from datetime import timedelta
from django.conf import settings
from ..models import *

from ..pm_py.process_miner import ProcessMiner
from pm4py.objects.log.importer.xes import importer as xes_importer
from ..pm_py import parameters
from jmetal.util.termination_criterion import *
from jmetal.algorithm.multiobjective.nsgaiii import UniformReferenceDirectionFactory


def is_log(event_log):
    try:
        log = xes_importer.apply(event_log)
        return True
    except:   
        return False 

def store_log(event_log):
    '''
    Guarda el log subido por el usuario en el sistema.
    '''

    file_name = event_log.name
    file_path = os.path.join(settings.LOGS_FOLDER, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb+') as destination:
        for chunk in event_log.chunks():
            destination.write(chunk)

    if not is_log(file_path):
        os.remove(file_path)
        raise Exception
        
    
    
def convert_to_serializable(obj):
    """Convierte un objeto a un formato serializable para almacenarlo en la base de datos"""
    if hasattr(obj, '__dict__'):
        return {key: convert_to_serializable(value) for key, value in obj.__dict__.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    else:
        return obj


def discover(execution_name, optimization_method, opt_parameters_dict, miner_type, evaluation_metrics, logpath):
    '''
    Ejecuta el proceso de descubrimiento con los datos aportados por el usuario.
    Guarda los resultados en la BD y genera la imagen del frente de pareto. 
    Devuelve el id de la ejecución.
    '''
    discovery_start = time()

    process_miner = ProcessMiner(miner_type=miner_type,
                    metrics=evaluation_metrics,
                    log = logpath)
                    
    if optimization_method == 'NSGAIII':
        metric_class = parameters.metrics_mapping[evaluation_metrics]
        metrics_labels = metric_class.get_labels()  
        reference_directions = UniformReferenceDirectionFactory(n_dim=len(metrics_labels), n_points=100)
        opt_parameters_dict['reference_directions']= reference_directions

    process_miner.discover(algorithm_name=optimization_method, **opt_parameters_dict, store=False)

    discovery_end = time()
    runtime = (discovery_end - discovery_start)
    runtime = timedelta(seconds=runtime)
    
    #### BBDD
    execution = Execution.objects.create(
        name = execution_name,
        runtime = runtime,
        path_events_log = logpath.split('/')[-1], # ruta relativa
        metrics = evaluation_metrics,
        miner = miner_type
    )
    execution.save()
    optimizer = Optimizer.objects.create(
        execution=execution,  
        name=optimization_method,  
        hip_params=convert_to_serializable(process_miner.extract_params())
    )
    optimizer.save()

    execution_result = process_miner.opt.get_result()
    non_dom_sols = process_miner.opt.get_non_dominated_sols()

    for solution in execution_result:
        solution_instance = DSolution.objects.create(
            variables = solution.variables,
            objectives = solution.objectives.tolist(),
            execution = execution,
            is_pareto = True if solution in non_dom_sols else False,
        )

        solution_instance.save()
    
    process_miner.opt.plot_pareto_front(title='Pareto front approximation', filename=os.path.join(settings.PARETO_PATH, f'pareto_front_{execution.id}'))
                                         
    return execution.id 

