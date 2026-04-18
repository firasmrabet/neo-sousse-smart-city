"""
Compilateur - Package principal
"""

__version__ = "1.0.0"
__author__ = "Firaz Mrabett"
__description__ = "Compilateur NL→SQL avec Automates et IA Générative"

from .compiler.compiler import Compiler
from .automata.engine import AutomataEngine
from .ia.report_generator import AIReportGenerator

__all__ = ["Compiler", "AutomataEngine", "AIReportGenerator"]
