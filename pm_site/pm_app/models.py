from django.db import models
    
class Execution(models.Model):
    name = models.CharField(max_length=100, help_text='Nombre de la ejecución')
    runtime = models.DurationField(help_text='tiempo de ejecución')
    path_events_log = models.CharField(max_length=2048)
    metrics = models.CharField(max_length=100)
    miner = models.CharField(max_length=100)

class Optimizer(models.Model):
    
    execution = models.OneToOneField(
        Execution,
        on_delete=models.CASCADE,
        primary_key=True
    )

    name = models.CharField(max_length=100)
    hip_params = models.JSONField()

class DSolution(models.Model):
    variables = models.JSONField()
    objectives = models.JSONField()
    execution = models.ForeignKey(Execution, on_delete=models.CASCADE)
    is_pareto = models.BooleanField(default=False)
