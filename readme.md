# MinerSweeper 

## Virtual environment usage

Para ejecutar el proyeto, se recomienda crear un entorno virtual, para ello ejecutar este comando en terminal.
(Nota: python3 en Linux)

```
python -m venv .venv
```

Una vez hecho se habrá creado un directorio (.venv/) con el entorno virtual, para activarlo:

```
source .venv/bin/activate
```

Una vez activado podemos instalar las dependencias del proyecto simplemente ejecutando este comando:

```
pip install -r requirements.txt
```

Y finalmente, para desactivarlo:

```
deactivate
```

Para lanzar el servidor ejecutar:

```
python pm_site/manage.py runserver
```