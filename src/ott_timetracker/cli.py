import holidays
import datetime
import argparse
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
import io
import sys
import os  # Import os for path manipulation

# === CONSTANTS ===
MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
COMMUNITY_CODE = "MD"
PDF_INPUT_PATH = os.path.join(os.path.dirname(__file__), "registro_jornada_laboral.pdf")  # Update path relative to the cli.py location within the package

# PDF Layout Constants
START_X_BY_PAGE = {
    "primera": 235,
    "intermedia": 83,
    "ultima": 83,
}
COL_WIDTH = 32
START_Y = 88
DIA_POSICION_Y = 0
ENTRADA_POSICION_Y = 43
SALIDA_POSICION_Y = 103
HORAS_POSICION_Y = 413
INCIDENCIA_POSICION_Y = 463
Y_OFFSET_EXTRA = 120

# === HELPER FUNCTIONS ===


def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Rellena el PDF de registro de jornada laboral.")
    parser.add_argument('--periodo', required=True, help="Mes y año en formato MM-YYYY")
    parser.add_argument('--inicio', type=int, required=False, help="Día en el que se comienzan a introducir datos", default=1)
    parser.add_argument('--incidencia', action='append', help="Texto de incidencia (puede repetirse, requiere --dias-incidencia)")
    parser.add_argument('--dias-incidencia', action='append', help="Rango de días para la incidencia en formato DD-DD (puede repetirse, requiere --incidencia)")
    parser.add_argument('--horario-incidencia', action='append', help="Horario de la incidencia en formato HH:MM-HH:MM (opcional, si no se indica se asume ausencia total)")
    parser.add_argument('--horas-trabajador', type=float, required=False, default=4.0, help="Número de horas de la jornada habitual del trabajador")
    parser.add_argument('--horario', type=str, required=False, default="15:00-19:00", help="Horario habitual del trabajador en formato HH:MM-HH:MM")
    args = parser.parse_args()

    # Sanitizar entradas de horario_incidencia eliminando comentarios tras '#'
    if args.horario_incidencia:
        args.horario_incidencia = [
            h.split('#', 1)[0].strip()
            for h in args.horario_incidencia
        ]
    return args


def setup_configuration_and_data(args):
    """Sets up configuration based on arguments and prepares necessary data."""
    try:
        month, year = map(int, args.periodo.split('-'))
    except ValueError:
        print("El periodo debe estar en formato MM-YYYY")
        sys.exit(1)

    nombre_mes = MESES_ES[month - 1]
    output_dir = "registros"
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
    pdf_output_path = os.path.join(output_dir, f"registro_jornada_laboral_{nombre_mes}{year}.pdf")

    spain_holidays = holidays.country_holidays('ES', subdiv=COMMUNITY_CODE, years=year)
    festivos = {d.day for d in spain_holidays if d.month == month}

    # Procesar incidencias
    incidencias_multi = {}
    if args.incidencia and args.dias_incidencia:
        horarios = args.horario_incidencia or []
        total = len(args.incidencia)
        # Pad horarios with None if fewer horarios than incidencias are provided
        if len(horarios) < total:
            horarios.extend([None] * (total - len(horarios)))  # Use extend instead of complex list comp

        for texto, rango, horario in zip(args.incidencia, args.dias_incidencia, horarios):
            try:
                inicio, fin = map(int, rango.split('-'))
                for d in range(inicio, fin + 1):
                    if d not in incidencias_multi:
                        incidencias_multi[d] = []
                    incidencias_multi[d].append({"texto": texto, "horario": horario})
            except ValueError:
                print(f"Rango de días inválido: {rango}")
                sys.exit(1)
            except Exception as e:
                print(f"Error procesando incidencia: {texto}, {rango}, {horario}. Error: {e}")
                sys.exit(1)

    # Días del mes que no son fin de semana ni festivo
    def dias_laborables_del_mes(year, month, festivos):
        dias = []
        num_days = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)).day if month < 12 else 31
        for day in range(1, num_days + 1):
            try:
                fecha = datetime.date(year, month, day)
                # Exclude weekends (Monday=0, Sunday=6)
                if fecha.weekday() < 5 and day not in festivos:
                    dias.append(day)
            except ValueError:  # Should not happen with num_days logic, but keep as safeguard
                break
        return dias

    dias_laborables = [d for d in dias_laborables_del_mes(year, month, festivos) if d >= args.inicio]
    dias_por_pagina = {
        "primera": dias_laborables[:10],
        "intermedia": dias_laborables[10:24],
        "ultima": dias_laborables[24:]
    }

    config = {
        "month": month,
        "year": year,
        "nombre_mes": nombre_mes,
        "pdf_output_path": pdf_output_path,
        "incidencias_multi": incidencias_multi,
        "dias_por_pagina": dias_por_pagina,
    }
    return config


def draw_rotated_text(can, text, x, y, angle=90, font="Helvetica", size=8):
    """Draws rotated text on the canvas."""
    can.saveState()
    can.translate(x, y)
    can.rotate(angle)
    can.setFont(font, size)
    can.drawString(0, 0, text)
    can.restoreState()


def calculate_worked_periods(horario_base_str, incidencias_dia):
    """Calculates the actual worked periods considering incidences."""
    horario_inicio_base, horario_fin_base = horario_base_str.split('-')
    h_jorn_ini = datetime.datetime.strptime(horario_inicio_base, "%H:%M")
    h_jorn_fin = datetime.datetime.strptime(horario_fin_base, "%H:%M")

    horarios_incidencia_parsed = []
    for inc in incidencias_dia:
        raw_horario = inc.get("horario")
        if raw_horario:
            clean_horario = raw_horario.split('#', 1)[0].strip()
            try:
                s, e = clean_horario.split('-')
                # Clamp incidence times to the base working hours
                dt_s = max(datetime.datetime.strptime(s, "%H:%M"), h_jorn_ini)
                dt_e = min(datetime.datetime.strptime(e, "%H:%M"), h_jorn_fin)
                if dt_s < dt_e:  # Only add valid, non-zero intervals
                    horarios_incidencia_parsed.append((dt_s, dt_e))
            except ValueError:
                print(f"Advertencia: Formato de horario de incidencia inválido '{raw_horario}', se ignora para el cálculo de horas.", file=sys.stderr)
                continue  # Skip invalid formats for calculation

    # Merge overlapping/adjacent incidence intervals
    horarios_incidencia_parsed.sort(key=lambda t: t[0])
    merged_incidencias = []
    for s, e in horarios_incidencia_parsed:
        if not merged_incidencias or s > merged_incidencias[-1][1]:
            merged_incidencias.append([s, e])
        else:
            merged_incidencias[-1][1] = max(merged_incidencias[-1][1], e)

    # Calculate worked periods (complement of incidences within base hours)
    worked_periods = []
    current_time = h_jorn_ini
    for start_inc, end_inc in merged_incidencias:
        if current_time < start_inc:
            worked_periods.append((current_time, start_inc))
        current_time = max(current_time, end_inc)

    if current_time < h_jorn_fin:
        worked_periods.append((current_time, h_jorn_fin))

    return worked_periods


def crear_overlay(tipo_pagina, dias_pagina, config, args):
    """Creates a PDF overlay layer with data for a specific page."""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=landscape(letter))
    x_inicial = START_X_BY_PAGE[tipo_pagina]

    if tipo_pagina == "primera":
        can.setFont("Helvetica", 8)
        draw_rotated_text(can, config["nombre_mes"].upper(), 193, 88)
        draw_rotated_text(can, str(config["year"]), 182, 90)

    horario_inicio_base, horario_fin_base = args.horario.split('-')

    for idx, day in enumerate(dias_pagina):
        x_base = x_inicial + idx * COL_WIDTH
        draw_rotated_text(can, str(day), x_base, START_Y + DIA_POSICION_Y)

        incidencias_dia = config["incidencias_multi"].get(day, [])

        if incidencias_dia:
            # Draw incidence text
            incidencia_texts = " + ".join([inc["texto"] for inc in incidencias_dia])
            draw_rotated_text(can, incidencia_texts, x_base, START_Y + INCIDENCIA_POSICION_Y)

            worked_periods = calculate_worked_periods(args.horario, incidencias_dia)

            y_off = 0
            total_horas_trabajadas = 0
            for start_work, end_work in worked_periods:
                if start_work < end_work:  # Ensure the period is valid
                    horas_periodo = round((end_work - start_work).total_seconds() / 3600, 2)
                    draw_rotated_text(can, start_work.strftime("%H:%M"), x_base, START_Y + ENTRADA_POSICION_Y + y_off)
                    draw_rotated_text(can, end_work.strftime("%H:%M"), x_base, START_Y + SALIDA_POSICION_Y + y_off)
                    total_horas_trabajadas += horas_periodo
                    y_off += Y_OFFSET_EXTRA  # Move down for next potential entry/exit pair

            # Draw the total hours worked for the day if > 0
            if total_horas_trabajadas > 0:
                draw_rotated_text(can, f"{total_horas_trabajadas:.2f}", x_base, START_Y + HORAS_POSICION_Y)
            # If total_horas_trabajadas is 0 (e.g., full day incidence), nothing is drawn for hours.

        else:  # No incidences for this day
            # Draw standard entry/exit times and total hours
            draw_rotated_text(can, horario_inicio_base, x_base, START_Y + ENTRADA_POSICION_Y)
            draw_rotated_text(can, horario_fin_base, x_base, START_Y + SALIDA_POSICION_Y)
            draw_rotated_text(can, f"{args.horas_trabajador:.2f}", x_base, START_Y + HORAS_POSICION_Y)

    can.save()
    packet.seek(0)
    return PdfReader(packet)


def generate_filled_pdf(config, args):
    """Generates the final PDF by merging overlays onto the template."""
    try:
        reader = PdfReader(PDF_INPUT_PATH)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo PDF base en '{PDF_INPUT_PATH}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error al leer el PDF base '{PDF_INPUT_PATH}': {e}")
        sys.exit(1)

    writer = PdfWriter()

    num_pages = len(reader.pages)
    for i, page in enumerate(reader.pages):
        if i == 0:
            tipo = "primera"
        elif i == num_pages - 1:
            tipo = "ultima"
        else:
            tipo = "intermedia"

        dias_pagina = config["dias_por_pagina"].get(tipo)
        if dias_pagina:  # Only create overlay if there are days for this page type
            try:
                overlay = crear_overlay(tipo, dias_pagina, config, args)
                page.merge_page(overlay.pages[0])
            except Exception as e:
                print(f"Error al crear o fusionar la capa para la página {i+1} ({tipo}): {e}")
                # Decide whether to exit or continue without overlay for this page
                # For now, let's continue but add the original page
                # sys.exit(1) # Uncomment to exit on overlay error

        writer.add_page(page)  # Add the (potentially merged) page

    try:
        with open(config["pdf_output_path"], "wb") as f:
            writer.write(f)
        print(f"PDF generado correctamente: {config['pdf_output_path']}")
    except Exception as e:
        print(f"Error al escribir el PDF final en '{config['pdf_output_path']}': {e}")
        sys.exit(1)


# === MAIN EXECUTION ===
def main():
    """Main function to orchestrate the PDF generation."""
    args = parse_arguments()
    config = setup_configuration_and_data(args)
    generate_filled_pdf(config, args)


if __name__ == "__main__":
    main()