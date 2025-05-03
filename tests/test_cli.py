import unittest
from unittest.mock import patch, MagicMock, call
import sys
import datetime
import os

# Add the 'src' directory to the Python path again to find the module
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Update imports for the new package and module name
from ott_timetracker.cli import (
    parse_arguments,
    calculate_worked_periods,
    setup_configuration_and_data,
    MESES_ES
)

# Rename the test class if desired (optional, but good practice)
class TestCli(unittest.TestCase):

    # Update patch targets if they refer to the old module name
    @patch('sys.argv', ['cli.py', '--periodo', '07-2024', '--horario', '09:00-13:00', '--horas-trabajador', '4.0'])
    def test_parse_arguments_basic(self):
        """Test basic argument parsing."""
        # ... (test logic remains the same) ...

    @patch('sys.argv', [
        'cli.py', # Update script name in mock argv if necessary
        '--periodo', '08-2024',
        '--inicio', '5',
        '--incidencia', 'Vacaciones', '--dias-incidencia', '15-15', '--horario-incidencia', '09:00-17:00',
        '--incidencia', 'Médico', '--dias-incidencia', '10-10', '--horario-incidencia', '10:00-11:00 # Cita'
    ])
    def test_parse_arguments_with_incidencias(self):
        """Test argument parsing with incidences and comments."""
        # ... (test logic remains the same) ...

    def test_calculate_worked_periods_no_incidencia(self):
        """Test work period calculation without incidences."""
        # ... (test logic remains the same) ...

    def test_calculate_worked_periods_single_incidencia_middle(self):
        """Test work period calculation with one incidence in the middle."""
        # ... (test logic remains the same) ...

    def test_calculate_worked_periods_full_day_incidencia(self):
        """Test work period calculation with a full day incidence."""
        # ... (test logic remains the same) ...

    def test_calculate_worked_periods_multiple_overlapping_incidencias(self):
        """Test work period calculation with multiple overlapping incidences."""
        # ... (test logic remains the same) ...

    def test_calculate_worked_periods_incidencia_outside_base(self):
        """Test incidences outside base working hours are ignored for calculation."""
        # ... (test logic remains the same) ...

    def test_calculate_worked_periods_incidencia_partial_overlap(self):
        """Test incidences partially overlapping base working hours are clamped."""
        # ... (test logic remains the same) ...

    # Update patch targets for the new module structure
    @patch('ott_timetracker.cli.holidays.country_holidays')
    @patch('ott_timetracker.cli.os.makedirs')
    @patch('ott_timetracker.cli.datetime')
    def test_setup_configuration_and_data(self, mock_datetime, mock_makedirs, mock_holidays):
        """Test the configuration setup and data preparation logic."""
        # ... (test logic remains the same, ensure args mock is appropriate) ...

        # Assertions remain the same, assuming config keys haven't changed
        # ... (assertions remain the same) ...

if __name__ == '__main__':
    unittest.main()
