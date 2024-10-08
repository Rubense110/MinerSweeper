from django import forms
from .models import *
import os
from django.conf import settings

class JsonImportForm(forms.Form):
    json_file = forms.FileField(
        label="Puedes importarla con su fichero JSON",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True
    )

class LogUploadForm(forms.Form):
    event_log = forms.FileField(
        label="Subir un nuevo Log de Eventos",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

class DiscoveryForm(forms.Form):
    OPTIMIZATION_METHODS = [
        ('NSGAII', 'NSGAII'),
        ('NSGAIII', 'NSGAIII'),
        ('SPEA2', 'SPEA2')
    ]
    
    MINER_TYPES = [
        ('heuristic', 'Heuristic Miner'),
        ('inductive', 'Inductive Miner'),
    ]
    
    METRICS = [
        ('basic', 'Basic metrics'),
        ('basic_useful_simple', 'Basic Useful Metrics'),
    ]
    
    execution_name = forms.CharField(
        label="Nombre", 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    optimization_method = forms.ChoiceField(
        choices=[('', '')] + OPTIMIZATION_METHODS,
        label="Método de Optimización",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    miner_type = forms.ChoiceField(
        choices=MINER_TYPES, 
        label="Tipo de Minero",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    event_log = forms.ChoiceField(
        label="Log de Eventos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    evaluation_metrics = forms.ChoiceField(
        choices=METRICS, 
        label="Métricas de Evaluación",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    ## Hiperparametros

    population_size = forms.IntegerField(
        required=False,
        label="Tamaño de Población",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    offspring_population_size = forms.IntegerField(
        required=False,
        label="Tamaño de Población de Descendencia",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    mutation_type = forms.ChoiceField(
        required=False,
        choices=[('polynomial', 'Polynomial Mutation'),
                 ('random', 'Random Mutation'),
                 ('uniform', 'Uniform Mutation'),
                 ('non_uniform', 'Non-Uniform Mutation'),],
        label="Tipo de Mutación",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mutation_probability = forms.FloatField(
        required=False,
        label="Probabilidad de Mutación",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    crossover_type = forms.ChoiceField(
        required=False,
        choices=[('pmx', 'PMX Crossover'), ('sbx', 'SBX Crossover')],
        label="Tipo de Crossover",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    crossover_probability = forms.FloatField(
        required=False,
        label="Probabilidad de Crossover",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    max_evaluations = forms.IntegerField(
        required=False,
        label="Número de Evaluaciones",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        log_files = [(f, f) for f in os.listdir(settings.LOGS_FOLDER) if os.path.isfile(os.path.join(settings.LOGS_FOLDER, f))]
        self.fields['event_log'].choices = log_files

    def clean(self):
        cleaned_data = super().clean()
        optimization_method = cleaned_data.get("optimization_method")

        if optimization_method in ['NSGAII', 'SPEA2']:
            if not cleaned_data.get('offspring_population_size'):
                self.add_error('offspring_population_size', 'campo obligatorio')

        if optimization_method in ['NSGAII', 'NSGAIII', 'SPEA2']:
            if not cleaned_data.get('mutation_type'):
                self.add_error('mutation_type', 'campo obligatorio')
            if not cleaned_data.get('mutation_probability'):
                self.add_error('mutation_probability', 'campo obligatorio')
            if not cleaned_data.get('crossover_type'):
                self.add_error('crossover_type', 'campo obligatorio')
            if not cleaned_data.get('crossover_probability'):
                self.add_error('crossover_probability', 'campo obligatorio')
            if not cleaned_data.get('max_evaluations'):
                self.add_error('max_evaluations', 'campo obligatorio')

        return cleaned_data