from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.core.paginator import Paginator
import traceback
from .models import DSolution, Execution  
import os
from .forms import DiscoveryForm, LogUploadForm, JsonImportForm
from .utils.discovery import *
from .pm_py import parameters
from .utils.petri import get_petri_net
from .utils.hiperparameters import get_hipparam_dict
import io
import csv
import json
import zipfile
from django.contrib import messages
from .utils.JSON_importer import import_from_json

def history(request):
    query = request.GET.get('query', '')
    filter_option = request.GET.get('filter_option', 'no_filter')

    executions = Execution.objects.all()

    if query:
        if filter_option == 'name':
            executions = executions.filter(name__icontains=query)
        elif filter_option == 'miner':
            executions = executions.filter(miner__icontains=query)
        elif filter_option == 'optimizer':
            executions = executions.filter(optimizer__name__icontains=query)
        elif filter_option == 'log':
            executions = executions.filter(path_events_log__icontains=query)
        elif filter_option == 'metrics':
            executions = executions.filter(metrics__icontains=query)
        elif filter_option == 'id':
            try:
                executions = executions.filter(id=query)
            except ValueError:
                pass 

    paginator = Paginator(executions, 10)
    page_number = request.GET.get('page')
    executions_to_show = paginator.get_page(page_number)

    return render(request, 'history.html', 
                  {'executions': executions_to_show, 
                   'query': query, 'filter_option': filter_option})

def delete_execution(request, execution_id):
    execution = get_object_or_404(Execution, id=execution_id)
    optimizer = Optimizer.objects.filter(execution=execution).first()
    if optimizer:
        optimizer.delete()
    DSolution.objects.filter(execution=execution).delete()
    execution.delete()
    messages.info(request, f'Eliminada la ejecución {execution.name}')
    return redirect('history') 

def intro(request):
    return render(request, 'intro.html')

def manual(request):
    return render(request, 'manual.html')

def discovery(request):
    error_msg = "Error en el proceso de descubrimiento. Por favor, inténtelo de nuevo."    
    log_dir = settings.LOGS_FOLDER
    log_files = []
    if os.path.exists(log_dir):
        log_files = os.listdir(log_dir)
        if request.method == 'POST':
            form = DiscoveryForm(request.POST)
            if form.is_valid():
                try:
                    execution_name = form.cleaned_data['execution_name']  
                    optimization_method = form.cleaned_data['optimization_method']
                    selected_log = form.cleaned_data['event_log']  
                    miner_type = form.cleaned_data['miner_type']
                    evaluation_metrics = form.cleaned_data['evaluation_metrics']

                    opt_parameters_dict = get_hipparam_dict(form.cleaned_data)
                    logpath = os.path.join(log_dir, selected_log)

                    execution_id = discover(execution_name, optimization_method, 
                                                opt_parameters_dict, miner_type, 
                                                evaluation_metrics, logpath)
                    return redirect('discovery_result', execution_id)
                except Exception as e:
                    print(f"Error durante el descubrimiento: {e}")
                    print(traceback.format_exc())

                    return render(request, 'discovery_error.html', {
                        'error_message': error_msg,
                        'exception' : e
                    })
                    
            else:
                return render(request, 'discovery_error.html', {
                    'error_message': error_msg,
                    'exception' : 'Formulario no válido.'
                })
        else:
            form = DiscoveryForm()
        
    return render(request, 'discovery.html', {'form': form, 'log_files': log_files})

def discovery_result(request, execution_id):
    
    execution = Execution.objects.get(pk=execution_id)
    optimizer = execution.optimizer

    execution_name = execution.name
    miner_type = execution.miner
    evaluation_metrics = execution.metrics
    events_log = execution.path_events_log
    runtime = execution.runtime
    optimization_method = optimizer.name
    optimization_hipparams = optimizer.hip_params
    
    return render(request, 'discovery_results.html', {
        'execution_name': execution_name,  
        'events_log': events_log,  
        'miner_type': miner_type,  
        'evaluation_metrics': evaluation_metrics,  
        'runtime': runtime,  
        'optimization_method': optimization_method,  
        'optimization_hipparams': optimization_hipparams,
        'execution_id': execution.id, 
    })

def solutions(request, execution_id):
    execution = get_object_or_404(Execution, pk=execution_id)
    dsolutions = DSolution.objects.filter(execution=execution)

    pareto_front_path = None

    if request.GET.get('filter') == 'pareto':
        dsolutions = DSolution.objects.filter(execution=execution, is_pareto = True)
        pareto_front_path = f'{settings.PARETO_URL}pareto_front_{execution.id}.png'
        

    paginator = Paginator(dsolutions, 10) 
    page_number = request.GET.get('page')  
    solutions_to_show = paginator.get_page(page_number)  

    ids = list(range(len(dsolutions)))

    evaluation_metrics = execution.metrics
    miner = execution.miner

    miner_params = parameters.parameter_mapping[miner]
    miner_params_names = miner_params.get_param_names()

    metric_class = parameters.metrics_mapping[evaluation_metrics]
    metrics_labels = metric_class.get_labels()  

    return render(request, 'solutions.html', {
        'execution': execution,
        'solutions': solutions_to_show,
        'metrics_labels': metrics_labels,
        'miner_params_names': miner_params_names,
        'ids' : ids,
        'pareto_image_path' : pareto_front_path
    })


 
def solution_details(request, solution_id):
    solution = get_object_or_404(DSolution, id=solution_id)
    execution = solution.execution
    evaluation_metrics = execution.metrics

    miner_params = parameters.parameter_mapping[execution.miner]
    miner_params_names = miner_params.get_param_names()

    metric_class = parameters.metrics_mapping[evaluation_metrics]
    metrics_labels = metric_class.get_labels()  

    petri_net_img_b64 = get_petri_net(solution.id)

    return render(request, 'solution_details.html', {
        'solution': solution,
        'execution': execution,
        'metrics_labels': metrics_labels,
        'miner_params_names': miner_params_names,
        'petri_net_image_base64': petri_net_img_b64,
    })

def get_execution_data(_,execution_id):

    execution = get_object_or_404(Execution, pk=execution_id)
    solutions = DSolution.objects.filter(execution=execution)
    optimizer = execution.optimizer

    miner_params = parameters.parameter_mapping[execution.miner]
    miner_params_names = miner_params.get_param_names()

    metric_class = parameters.metrics_mapping[execution.metrics]
    metrics_labels = metric_class.get_labels()  
    

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip:
        csv_solution_variables = io.StringIO()
        writer = csv.writer(csv_solution_variables)
        writer.writerow(miner_params_names)
        for sol in solutions:
            writer.writerow(sol.variables)
        zip.writestr('sol_variables.csv', csv_solution_variables.getvalue())

        csv_solution_objectives = io.StringIO()
        writer = csv.writer(csv_solution_objectives)
        writer.writerow(metrics_labels)
        for sol in solutions:
            writer.writerow(sol.objectives)
        zip.writestr('sol_objectives.csv', csv_solution_objectives.getvalue())

        execution_data = {
            'execution': {
                'name': execution.name,
                'path_events_log': execution.path_events_log,
                'metrics': execution.metrics,
                'miner': execution.miner,
            },
            'optimizer': {
                'name': optimizer.name,
                'hip_params': optimizer.hip_params 
            }
        }
        execution_json = json.dumps(execution_data, indent=4)

        zip.writestr('execution_data.json', execution_json)

    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename=execution_{execution_id}_{execution.name}.zip'
    
    return response

def logs(request):
    log_dir = settings.LOGS_FOLDER 
    if request.method == 'POST':
        log_upload_form = LogUploadForm(request.POST, request.FILES)
        if log_upload_form.is_valid():
            event_log = request.FILES['event_log']
            try:
                store_log(event_log)
                return redirect('logs')
            except Exception as e:
                messages.warning(request, 'El archivo subido no es un log de eventos')
                return redirect('logs')
    
        log_to_delete = request.POST.get('log_to_delete')
        if log_to_delete:
            log_path = os.path.join(log_dir, log_to_delete)
            if os.path.exists(log_path):
                os.remove(log_path)
                log_name = log_path.split('/')[-1]
                messages.info(request, f'Eliminado el log {log_name}')
                return redirect('logs') 
    else:
        log_upload_form = LogUploadForm()

    logs = os.listdir(log_dir) if os.path.exists(log_dir) else []

    return render(request, 'logs.html', {
        'log_upload_form': log_upload_form,
        'logs': logs
    })

def json_import(request):
    if request.method == 'POST':
        form = JsonImportForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = form.cleaned_data['json_file']
            try:
                json_data = json.load(json_file)
                try:
                    POST_form_data = import_from_json(json_data)
                except Exception as e:
                    print(f"Error durante al importar JSON: {e}")
                    print(traceback.format_exc())

                    return render(request, 'discovery_error.html', {
                        'error_message': "Ha ocurrido un error importanto el fichero JSON."
                    })
                
                return render(request, 'import_json_redirect.html', {'post_data': POST_form_data})
            except:
                messages.warning(request, 'El archivo subido no es un JSON válido.')
    else:
        form = JsonImportForm()

    return render(request, 'json_import.html', {'form': form})