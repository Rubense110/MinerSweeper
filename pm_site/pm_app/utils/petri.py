from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.convert import convert_to_petri_net
from django.shortcuts import get_object_or_404
from ..models import DSolution
import io
import os
import base64
from ..pm_py.parameters import *
from django.conf import settings

def get_petri_net(solution_id):
    solution = get_object_or_404(DSolution, pk=solution_id)

    execution = solution.execution
    sol_variables = solution.variables
    miner_name = execution.miner

    parameters_class = parameter_mapping[miner_name]
    miner_params = {key: sol_variables[idx] for idx, key in enumerate(parameters_class.param_range.keys())}
    miner_class = miner_mapping[miner_name]
    event_log_path = os.path.join(settings.LOGS_FOLDER, execution.path_events_log)
    log = xes_importer.apply(event_log_path)

    petri_net, initial_marking, final_marking = generate_petri_net(miner_class, miner_params, log)

    gviz = pn_visualizer.apply(petri_net, initial_marking, final_marking)

    buffer = io.BytesIO(gviz.pipe('png'))
    img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return img_b64

def generate_petri_net(miner_class, miner_params, log):

    if miner_class == heuristics_miner:
        petri, initial_marking, final_marking = miner_class.apply(log, parameters= miner_params)

    elif miner_class == inductive_miner:
        inductive_variant = inductive_miner.Variants.IMf if miner_params["noise_threshold"] > 0 else inductive_miner.Variants.IM
        miner_params["multi_processing"] = True if miner_params["multi_processing"] > 0.5 else False
        miner_params["disable_fallthroughs"] = True if miner_params["disable_fallthroughs"] > 0.5 else False

        process_tree = miner_class.apply(log, variant = inductive_variant,  parameters= miner_params )
        petri, initial_marking, final_marking = convert_to_petri_net(process_tree)  

    return petri, initial_marking, final_marking