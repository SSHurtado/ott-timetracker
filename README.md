# OTT Timetracker

Este script genera partes de horas en PDF rellenados automáticamente basados en los parámetros proporcionados.

## Importante

Antes de usar el script, **debes modificar manualmente el archivo PDF base** que se encuentra en `src/ott_timetracker/media/registro_jornada_laboral.pdf`.

Asegúrate de añadir tu nombre y el nombre del investigador/a principal en los campos correspondientes dentro del PDF. El script **no** modifica estos campos.

## Ejemplo de Uso

```bash
python3 -m ott_timetracker \
  --periodo 05-2025 \
  --inicio 4 \
  --horas-trabajador 6 \
  --horario "08:00-14:00" \
  --incidencia "Vacaciones" --dias-incidencia 10-12 \
  --incidencia "Reducción" --dias-incidencia 20-20 --horario-incidencia "08:00-12:00" \
  --incidencia "Horas libres" --dias-incidencia 21-21 --horario-incidencia "10:00-12:00" \
  --incidencia "Reducción Enfermedad" --dias-incidencia 22-22 --horario-incidencia "09:00-10:00" \
  --incidencia "Reducción Enfermedad" --dias-incidencia 22-22 --horario-incidencia "12:00-13:00"
```

**Nota:** Asegúrate de ejecutar el comando desde el directorio raíz del proyecto (`ott-timetracker`) y de tener el entorno virtual activado si es necesario.

### Recomendación

Para facilitar la ejecución repetida del comando con diferentes parámetros, se recomienda crear un archivo de script shell (por ejemplo, `run_timetracker.sh`) con el comando y modificar los parámetros según sea necesario antes de ejecutarlo.
