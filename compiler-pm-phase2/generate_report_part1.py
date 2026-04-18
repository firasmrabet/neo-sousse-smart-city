"""
Rapport PDF — SensorLinker Neo-Sousse Smart City
Part 1: Classes de base et utilitaires PDF
"""
from fpdf import FPDF
import os, datetime

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))

class SmartCityPDF(FPDF):
    """PDF professionnel avec en-tête/pied de page"""
    
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=25)
        self._chapter_num = 0
        self._section_num = 0
        self._toc_entries = []
        self._current_chapter = ""
    
    def header(self):
        if self.page_no() <= 2:
            return
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'SensorLinker - Plateforme Smart City avec Compilation et IA', 0, 0, 'L')
        self.cell(0, 8, f'Page {self.page_no()}', 0, 1, 'R')
        self.set_draw_color(0, 102, 204)
        self.set_line_width(0.5)
        self.line(10, 15, 200, 15)
        self.ln(5)
    
    def footer(self):
        if self.page_no() <= 2:
            return
        self.set_y(-20)
        self.set_draw_color(0, 102, 204)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'Neo-Sousse Smart City 2030 | Module: Theorie des Langages et Compilation | 2025-2026', 0, 0, 'C')
    
    def cover_page(self):
        """Page de garde professionnelle"""
        self.add_page()
        # Bande bleue en haut
        self.set_fill_color(0, 51, 102)
        self.rect(0, 0, 210, 45, 'F')
        self.set_fill_color(0, 102, 204)
        self.rect(0, 45, 210, 3, 'F')
        
        # Logo/Titre universite
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.set_y(10)
        self.cell(0, 8, 'Universite de Sousse', 0, 1, 'C')
        self.set_font('Helvetica', '', 11)
        self.cell(0, 7, 'Institut Superieur des Sciences Appliquees et de Technologie de Sousse', 0, 1, 'C')
        self.cell(0, 7, 'Departement Informatique', 0, 1, 'C')
        
        # Titre principal
        self.set_y(70)
        self.set_text_color(0, 51, 102)
        self.set_font('Helvetica', 'B', 28)
        self.cell(0, 15, 'SensorLinker', 0, 1, 'C')
        
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 102, 204)
        self.cell(0, 12, 'Plateforme Smart City avec', 0, 1, 'C')
        self.cell(0, 12, 'Compilation et IA Generative', 0, 1, 'C')
        
        # Ligne decorative
        self.set_draw_color(0, 102, 204)
        self.set_line_width(1)
        self.line(60, 115, 150, 115)
        
        # Sous-titre
        self.set_y(122)
        self.set_font('Helvetica', '', 12)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, 'Module : Theorie des Langages et Compilation', 0, 1, 'C')
        self.cell(0, 8, 'Annee Universitaire : 2025 - 2026', 0, 1, 'C')
        
        # Cadre infos
        self.set_y(155)
        self.set_fill_color(240, 244, 248)
        self.set_draw_color(0, 102, 204)
        self.rect(30, 155, 150, 55, 'DF')
        
        self.set_y(160)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, 'Realise par :', 0, 1, 'C')
        self.set_font('Helvetica', '', 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 7, 'Firas MRABET', 0, 1, 'C')
        self.ln(3)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, 'Encadre par :', 0, 1, 'C')
        self.set_font('Helvetica', '', 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 7, 'Enseignant du Module TLC', 0, 1, 'C')
        
        # Bande bleue en bas
        self.set_fill_color(0, 51, 102)
        self.rect(0, 270, 210, 27, 'F')
        self.set_y(275)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(255, 255, 255)
        now = datetime.datetime.now()
        self.cell(0, 8, f'Avril {now.year} | Sousse, Tunisie', 0, 1, 'C')
    
    def add_toc(self):
        """Table des matieres"""
        self.add_page()
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(0, 51, 102)
        self.cell(0, 15, 'Table des Matieres', 0, 1, 'C')
        self.ln(10)
        
        toc_items = [
            ("1", "Introduction Generale", 3),
            ("1.1", "   Contexte du projet", 3),
            ("1.2", "   Objectifs", 3),
            ("1.3", "   Technologies utilisees", 4),
            ("2", "Architecture du Systeme", 5),
            ("2.1", "   Architecture globale", 5),
            ("2.2", "   Structure du projet", 6),
            ("2.3", "   Base de donnees", 7),
            ("3", "Compilateur NL vers SQL", 9),
            ("3.1", "   Analyse Lexicale (Lexer)", 9),
            ("3.2", "   Analyse Syntaxique (Parser)", 11),
            ("3.3", "   Analyse Semantique", 13),
            ("3.4", "   Generation de Code SQL", 14),
            ("3.5", "   Schema Registry", 15),
            ("4", "Automates a Etats Finis", 16),
            ("4.1", "   Formalisme DFA", 16),
            ("4.2", "   Automate Capteur IoT", 17),
            ("4.3", "   Automate Intervention", 18),
            ("4.4", "   Automate Vehicule", 19),
            ("4.5", "   Moteur d'Alertes", 20),
            ("5", "Intelligence Artificielle", 21),
            ("5.1", "   Architecture IA", 21),
            ("5.2", "   Rapports Qualite de l'Air", 22),
            ("5.3", "   Validation d'Interventions", 23),
            ("5.4", "   Generation de PDF", 24),
            ("6", "Dashboard et Interface", 25),
            ("6.1", "   Dashboard Streamlit", 25),
            ("6.2", "   Authentification Google OAuth", 26),
            ("6.3", "   Simulation Temps Reel", 27),
            ("6.4", "   Dashboard React", 28),
            ("7", "Base de Donnees Detaillee", 29),
            ("7.1", "   Schema relationnel", 29),
            ("7.2", "   Tables et relations", 30),
            ("8", "Tests et Validation", 32),
            ("9", "Conclusion et Perspectives", 34),
        ]
        
        for num, title, page in toc_items:
            if len(num) <= 1:
                self.set_font('Helvetica', 'B', 11)
                self.set_text_color(0, 51, 102)
            else:
                self.set_font('Helvetica', '', 10)
                self.set_text_color(60, 60, 60)
            
            dots = '.' * (60 - len(title))
            self.cell(0, 7, f'{num}  {title} {dots} {page}', 0, 1, 'L')
    
    def chapter_title(self, title):
        """Titre de chapitre"""
        self._chapter_num += 1
        self._section_num = 0
        self._current_chapter = title
        self.add_page()
        
        # Bande coloree
        self.set_fill_color(0, 51, 102)
        self.rect(10, 20, 190, 1.5, 'F')
        
        self.set_y(25)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, f'Chapitre {self._chapter_num}', 0, 1, 'L')
        
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 102, 204)
        self.cell(0, 10, title, 0, 1, 'L')
        
        self.set_fill_color(0, 102, 204)
        self.rect(10, self.get_y() + 2, 60, 0.8, 'F')
        self.ln(10)
    
    def section_title(self, title):
        """Titre de section"""
        self._section_num += 1
        self.ln(5)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(0, 51, 102)
        self.cell(0, 9, f'{self._chapter_num}.{self._section_num}  {title}', 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 100, self.get_y())
        self.ln(4)
    
    def body_text(self, text):
        """Texte du corps"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(3)
    
    def bullet_list(self, items):
        """Liste a puces"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(40, 40, 40)
        for item in items:
            x_start = self.get_x()
            self.set_x(15)
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(0, 102, 204)
            self.cell(6, 6, '>', 0, 0)
            self.set_font('Helvetica', '', 10)
            self.set_text_color(40, 40, 40)
            self.multi_cell(170, 6, item)
        self.ln(2)
    
    def code_block(self, code, title=""):
        """Bloc de code"""
        if title:
            self.set_font('Helvetica', 'BI', 9)
            self.set_text_color(0, 102, 204)
            self.cell(0, 6, title, 0, 1)
        
        self.set_fill_color(245, 245, 250)
        self.set_draw_color(200, 200, 220)
        
        lines = code.split('\n')
        h = len(lines) * 5 + 6
        
        if self.get_y() + h > 270:
            self.add_page()
        
        y_start = self.get_y()
        self.rect(12, y_start, 186, h, 'DF')
        
        self.set_font('Courier', '', 8)
        self.set_text_color(30, 30, 30)
        self.set_y(y_start + 3)
        for line in lines:
            self.set_x(15)
            self.cell(0, 5, line[:95], 0, 1)
        self.ln(4)
    
    def info_box(self, title, content):
        """Boite d'information coloree"""
        if self.get_y() > 250:
            self.add_page()
        y = self.get_y()
        self.set_fill_color(230, 240, 255)
        self.set_draw_color(0, 102, 204)
        self.rect(12, y, 186, 25, 'DF')
        self.set_xy(15, y + 3)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(0, 51, 102)
        self.cell(0, 6, title, 0, 1)
        self.set_x(15)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(180, 5, content)
        self.set_y(y + 28)
    
    def table(self, headers, rows, col_widths=None):
        """Tableau professionnel"""
        if not col_widths:
            w = 190 / len(headers)
            col_widths = [w] * len(headers)
        
        if self.get_y() + 10 + len(rows) * 7 > 270:
            self.add_page()
        
        # Header
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, 1, 0, 'C', True)
        self.ln()
        
        # Rows
        self.set_font('Helvetica', '', 8)
        self.set_text_color(40, 40, 40)
        for r_idx, row in enumerate(rows):
            if r_idx % 2 == 0:
                self.set_fill_color(245, 248, 252)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 7, str(cell)[:30], 1, 0, 'L', True)
            self.ln()
        self.ln(5)


if __name__ == "__main__":
    print("Part 1 OK - Classes de base chargees")
