"""
Composants Visuels Avancés pour Documents Word OptimPV
Bibliothèque de composants design réutilisables de niveau agence
"""

import io
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import math

try:
    from docx import Document
    from docx.shared import Inches, RGBColor, Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml.shared import OxmlElement, qn
    from docx.oxml.ns import nsdecls
    from docx.oxml import parse_xml
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    # Créer des classes mock pour éviter NameError
    class Document:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    class RGBColor:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    class Inches:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    class Pt:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    class Cm:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    # Mock pour les enums
    WD_ALIGN_PARAGRAPH = None
    WD_BREAK = None
    WD_TABLE_ALIGNMENT = None
    WD_ALIGN_VERTICAL = None
    OxmlElement = None
    qn = None
    nsdecls = None
    parse_xml = None

from .professional_template_engine import ProfessionalTemplateEngine


class VisualComponents:
    """
    Bibliothèque de composants visuels premium pour documents Word
    Niveau de qualité : Design d'agence professionnelle
    """
    
    def __init__(self):
        """Initialise avec le moteur de templates professionnel"""
        self.template_engine = ProfessionalTemplateEngine()
        self.colors = self.template_engine.colors
        self.typography = self.template_engine.typography
    
    def create_executive_summary_layout(self, doc: Document, title: str, 
                                      key_points: List[str], metrics: Dict[str, str]) -> None:
        """
        Crée un layout de résumé exécutif avec design magazine
        
        Layout: Titre + 3 colonnes (points clés + métriques visuelles)
        """
        
        # 📰 TITRE EXECUTIVE STYLE
        self.template_engine.create_section_header(doc, "★", title, "📊")
        
        # 🏗️ LAYOUT 3 COLONNES
        main_table = doc.add_table(rows=1, cols=3)
        main_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Configuration des largeurs
        col1 = main_table.cell(0, 0)
        col2 = main_table.cell(0, 1) 
        col3 = main_table.cell(0, 2)
        
        col1.width = Cm(6)    # Points clés
        col2.width = Cm(1)    # Séparateur
        col3.width = Cm(9)    # Métriques
        
        # 📋 COLONNE 1: POINTS CLÉS
        self._set_cell_margins(col1, Pt(16), Pt(16), Pt(16), Pt(16))
        self._set_cell_background(col1, self.colors['neutral_50'])
        
        points_para = col1.paragraphs[0]
        title_run = points_para.add_run("🎯 POINTS CLÉS\n\n")
        title_run.font.size = Pt(12)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['primary']
        
        for i, point in enumerate(key_points[:4]):  # Max 4 points
            point_para = col1.add_paragraph()
            bullet_run = point_para.add_run(f"▪ ")
            bullet_run.font.color.rgb = self.colors['accent']
            bullet_run.font.bold = True
            
            point_run = point_para.add_run(point)
            point_run.font.size = Pt(10)
            point_run.font.color.rgb = self.colors['neutral_700']
        
        # 🎨 COLONNE 2: SÉPARATEUR DÉCORATIF
        self._set_cell_background(col2, self.colors['white'])
        sep_para = col2.paragraphs[0]
        sep_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Ligne verticale simulée avec caractères
        for i in range(10):
            sep_para.add_run("▌\n").font.color.rgb = self.colors['accent']
        
        # 📊 COLONNE 3: MÉTRIQUES VISUELLES 
        self._set_cell_margins(col3, Pt(16), Pt(16), Pt(16), Pt(16))
        
        metrics_grid = self._create_metrics_grid(col3, metrics)
        
        doc.add_paragraph()
    
    def create_comparison_showcase(self, doc: Document, title: str,
                                 before_data: Dict[str, str], after_data: Dict[str, str],
                                 savings_highlight: str) -> None:
        """
        Crée une présentation de comparaison AVANT/APRÈS impactante
        
        Design: Deux colonnes avec flèche centrale et highlight des économies
        """
        
        # 🏆 TITRE AVEC BANNIÈRE
        self.template_engine.create_section_header(doc, "⚖", title, "📈")
        
        # 🎨 LAYOUT COMPARAISON
        comp_table = doc.add_table(rows=2, cols=3)
        comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # === LIGNE 1: EN-TÊTES ===
        # AVANT header
        before_cell = comp_table.cell(0, 0)
        before_cell.width = Cm(7)
        self._set_cell_background(before_cell, self.colors['danger'])
        self._set_cell_margins(before_cell, Pt(16), Pt(16), Pt(20), Pt(20))
        
        before_para = before_cell.paragraphs[0]
        before_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        before_run = before_para.add_run("❌ SITUATION ACTUELLE")
        before_run.font.size = Pt(14)
        before_run.font.bold = True
        before_run.font.color.rgb = self.colors['white']
        
        # FLÈCHE centrale
        arrow_cell = comp_table.cell(0, 1)
        arrow_cell.width = Cm(2)
        self._set_cell_background(arrow_cell, self.colors['accent'])
        
        arrow_para = arrow_cell.paragraphs[0]
        arrow_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        arrow_run = arrow_para.add_run("➤")
        arrow_run.font.size = Pt(24)
        arrow_run.font.color.rgb = self.colors['white']
        
        # APRÈS header
        after_cell = comp_table.cell(0, 2)
        after_cell.width = Cm(7)
        self._set_cell_background(after_cell, self.colors['success'])
        self._set_cell_margins(after_cell, Pt(16), Pt(16), Pt(20), Pt(20))
        
        after_para = after_cell.paragraphs[0]
        after_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        after_run = after_para.add_run("✅ AVEC OPTIMPV")
        after_run.font.size = Pt(14)
        after_run.font.bold = True
        after_run.font.color.rgb = self.colors['white']
        
        # === LIGNE 2: CONTENU ===
        # AVANT contenu
        before_content = comp_table.cell(1, 0)
        self._set_cell_background(before_content, RGBColor(254, 242, 242))  # Rouge très clair
        self._set_cell_margins(before_content, Pt(20), Pt(20), Pt(20), Pt(20))
        
        self._fill_comparison_content(before_content, before_data, self.colors['danger'])
        
        # ÉCONOMIES highlight centrale
        savings_content = comp_table.cell(1, 1)
        self._set_cell_background(savings_content, self.colors['accent_light'])
        self._set_cell_margins(savings_content, Pt(20), Pt(20), Pt(10), Pt(10))
        
        savings_para = savings_content.paragraphs[0]
        savings_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Icône économie
        icon_run = savings_para.add_run("💰\n")
        icon_run.font.size = Pt(20)
        
        # Montant
        amount_run = savings_para.add_run(f"{savings_highlight}\n")
        amount_run.font.size = Pt(16)
        amount_run.font.bold = True
        amount_run.font.color.rgb = self.colors['accent_dark']
        
        # Label
        label_run = savings_para.add_run("ÉCONOMIE")
        label_run.font.size = Pt(10)
        label_run.font.bold = True
        label_run.font.color.rgb = self.colors['accent_dark']
        
        # APRÈS contenu
        after_content = comp_table.cell(1, 2)
        self._set_cell_background(after_content, RGBColor(240, 253, 244))  # Vert très clair
        self._set_cell_margins(after_content, Pt(20), Pt(20), Pt(20), Pt(20))
        
        self._fill_comparison_content(after_content, after_data, self.colors['success'])
        
        doc.add_paragraph()
    
    def create_timeline_visual(self, doc: Document, title: str, 
                             timeline_items: List[Dict[str, str]]) -> None:
        """
        Crée une timeline visuelle moderne avec étapes colorées
        
        Format timeline_items: [{"step": "1", "title": "Étape", "description": "...", "duration": "1 semaine"}]
        """
        
        # 🕒 TITRE TIMELINE
        self.template_engine.create_section_header(doc, "⏱", title, "🗓")
        
        # 🛤 TIMELINE PRINCIPALE
        for i, item in enumerate(timeline_items):
            self._create_timeline_step(doc, item, i, len(timeline_items))
        
        doc.add_paragraph()
    
    def create_metrics_dashboard(self, doc: Document, title: str,
                               metrics: Dict[str, Dict[str, str]]) -> None:
        """
        Crée un dashboard de métriques style KPI moderne
        
        Format metrics: {"metric_name": {"value": "42%", "label": "Autonomie", "icon": "🔋"}}
        """
        
        # 📊 TITRE DASHBOARD
        self.template_engine.create_section_header(doc, "📈", title, "📊")
        
        # 🏗️ GRILLE MÉTRIQUES (2x2 ou 3x3 selon le nombre)
        num_metrics = len(metrics)
        cols = 3 if num_metrics > 4 else 2
        rows = math.ceil(num_metrics / cols)
        
        dashboard_table = doc.add_table(rows=rows, cols=cols)
        dashboard_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        metric_items = list(metrics.items())
        
        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                if idx < len(metric_items):
                    metric_name, metric_data = metric_items[idx]
                    cell = dashboard_table.cell(row, col)
                    self._create_metric_card(cell, metric_data)
        
        doc.add_paragraph()
    
    def create_testimonial_showcase(self, doc: Document, testimonials: List[Dict[str, str]]) -> None:
        """
        Crée une vitrine de témoignages clients design
        
        Format: [{"quote": "...", "author": "Jean Dupont", "company": "ABC Corp", "rating": "5"}]
        """
        
        # 💬 TITRE TÉMOIGNAGES
        self.template_engine.create_section_header(doc, "💬", "Ils Nous Font Confiance", "⭐")
        
        for testimonial in testimonials[:3]:  # Max 3 témoignages
            self._create_testimonial_card(doc, testimonial)
        
        doc.add_paragraph()
    
    def create_process_flow(self, doc: Document, title: str, 
                          steps: List[Dict[str, str]]) -> None:
        """
        Crée un diagramme de processus horizontal moderne
        
        Format steps: [{"number": "1", "title": "Étape", "description": "..."}]
        """
        
        # 🔄 TITRE PROCESSUS
        self.template_engine.create_section_header(doc, "🔄", title, "⚙")
        
        # ➡ FLOW HORIZONTAL
        flow_table = doc.add_table(rows=2, cols=len(steps) * 2 - 1)  # Étapes + flèches
        flow_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        for i, step in enumerate(steps):
            # Cellule étape (numéro)
            step_col = i * 2
            number_cell = flow_table.cell(0, step_col)
            self._create_process_step_number(number_cell, step["number"])
            
            # Cellule description
            desc_cell = flow_table.cell(1, step_col)
            self._create_process_step_description(desc_cell, step["title"], step["description"])
            
            # Flèche (sauf dernière étape)
            if i < len(steps) - 1:
                arrow_col = step_col + 1
                arrow_cell = flow_table.cell(0, arrow_col)
                self._create_process_arrow(arrow_cell)
                
                # Cellule vide sous la flèche
                empty_cell = flow_table.cell(1, arrow_col)
                empty_cell.paragraphs[0].add_run(" ")
        
        doc.add_paragraph()
    
    def create_guarantee_badges(self, doc: Document, guarantees: List[Dict[str, str]]) -> None:
        """
        Crée des badges de garanties/certifications design
        
        Format: [{"icon": "🛡", "title": "Garantie 20 ans", "description": "..."}]
        """
        
        # 🛡 TITRE GARANTIES
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run("🛡 NOS GARANTIES & CERTIFICATIONS")
        title_run.font.size = Pt(16)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['primary']
        
        doc.add_paragraph()
        
        # 🏆 BADGES EN LIGNE
        cols = min(len(guarantees), 3)  # Max 3 par ligne
        badges_table = doc.add_table(rows=1, cols=cols)
        badges_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        for i, guarantee in enumerate(guarantees[:cols]):
            cell = badges_table.cell(0, i)
            self._create_guarantee_badge(cell, guarantee)
        
        doc.add_paragraph()
    
    # ===============================
    # MÉTHODES PRIVÉES SPÉCIALISÉES
    # ===============================
    
    def _create_metrics_grid(self, parent_cell, metrics: Dict[str, str]) -> None:
        """Crée une grille de métriques dans une cellule"""
        
        # Titre de la grille
        title_para = parent_cell.paragraphs[0]
        title_run = title_para.add_run("📊 INDICATEURS CLÉS\n\n")
        title_run.font.size = Pt(12)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['primary']
        
        # Métriques en grille 2x2
        metric_items = list(metrics.items())
        for i in range(0, len(metric_items), 2):
            row_para = parent_cell.add_paragraph()
            
            # Première métrique de la ligne
            if i < len(metric_items):
                name1, value1 = metric_items[i]
                metric1_run = row_para.add_run(f"{value1}")
                metric1_run.font.size = Pt(18)
                metric1_run.font.bold = True
                metric1_run.font.color.rgb = self.colors['accent']
                
                label1_run = row_para.add_run(f"\n{name1}")
                label1_run.font.size = Pt(9)
                label1_run.font.color.rgb = self.colors['neutral_500']
                
                # Espacement
                row_para.add_run("    ")
            
            # Deuxième métrique de la ligne
            if i + 1 < len(metric_items):
                name2, value2 = metric_items[i + 1]
                metric2_run = row_para.add_run(f"{value2}")
                metric2_run.font.size = Pt(18)
                metric2_run.font.bold = True
                metric2_run.font.color.rgb = self.colors['secondary']
                
                label2_run = row_para.add_run(f"\n{name2}")
                label2_run.font.size = Pt(9)
                label2_run.font.color.rgb = self.colors['neutral_500']
            
            # Espacement entre les lignes
            parent_cell.add_paragraph()
    
    def _fill_comparison_content(self, cell, data: Dict[str, str], color: RGBColor) -> None:
        """Remplit le contenu d'une cellule de comparaison"""
        
        para = cell.paragraphs[0]
        
        for key, value in data.items():
            # Label
            label_run = para.add_run(f"{key}: ")
            label_run.font.size = Pt(10)
            label_run.font.bold = True
            label_run.font.color.rgb = self.colors['neutral_700']
            
            # Valeur
            value_run = para.add_run(f"{value}\n")
            value_run.font.size = Pt(12)
            value_run.font.bold = True
            value_run.font.color.rgb = color
    
    def _create_timeline_step(self, doc: Document, item: Dict[str, str], 
                            index: int, total: int) -> None:
        """Crée une étape de timeline"""
        
        # Table pour l'étape (numéro + contenu)
        step_table = doc.add_table(rows=1, cols=2)
        step_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        
        # Cellule numéro (cercle coloré)
        number_cell = step_table.cell(0, 0)
        number_cell.width = Cm(2)
        
        color = self.colors['primary'] if index % 2 == 0 else self.colors['accent']
        self._set_cell_background(number_cell, color)
        self._set_cell_margins(number_cell, Pt(12), Pt(12), Pt(12), Pt(12))
        
        number_para = number_cell.paragraphs[0]
        number_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        number_run = number_para.add_run(item["step"])
        number_run.font.size = Pt(16)
        number_run.font.bold = True
        number_run.font.color.rgb = self.colors['white']
        
        # Cellule contenu
        content_cell = step_table.cell(0, 1)
        self._set_cell_background(content_cell, self.colors['neutral_50'])
        self._set_cell_margins(content_cell, Pt(16), Pt(16), Pt(20), Pt(20))
        
        content_para = content_cell.paragraphs[0]
        
        # Titre
        title_run = content_para.add_run(f"{item['title']}")
        title_run.font.size = Pt(14)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['neutral_800']
        
        # Durée
        if "duration" in item:
            duration_run = content_para.add_run(f" ({item['duration']})")
            duration_run.font.size = Pt(10)
            duration_run.font.color.rgb = self.colors['accent']
        
        content_para.add_run(f"\n{item['description']}")
        
        # Connecteur vertical (sauf dernière étape)
        if index < total - 1:
            connector_para = doc.add_paragraph()
            connector_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            connector_run = connector_para.add_run("    ▼")
            connector_run.font.size = Pt(12)
            connector_run.font.color.rgb = self.colors['neutral_300']
    
    def _create_metric_card(self, cell, metric_data: Dict[str, str]) -> None:
        """Crée une carte métrique dans une cellule"""
        
        cell.width = Cm(5)
        self._set_cell_background(cell, self.colors['neutral_50'])
        self._add_cell_border(cell, self.colors['primary'])
        self._set_cell_margins(cell, Pt(20), Pt(20), Pt(16), Pt(16))
        
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Icône
        if "icon" in metric_data:
            icon_run = para.add_run(f"{metric_data['icon']}\n")
            icon_run.font.size = Pt(24)
        
        # Valeur
        value_run = para.add_run(f"{metric_data['value']}\n")
        value_run.font.size = Pt(20)
        value_run.font.bold = True
        value_run.font.color.rgb = self.colors['primary']
        
        # Label
        label_run = para.add_run(metric_data['label'])
        label_run.font.size = Pt(10)
        label_run.font.bold = True
        label_run.font.color.rgb = self.colors['neutral_600']
    
    def _create_testimonial_card(self, doc: Document, testimonial: Dict[str, str]) -> None:
        """Crée une carte de témoignage"""
        
        # Table témoignage
        test_table = doc.add_table(rows=2, cols=1)
        test_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Citation
        quote_cell = test_table.cell(0, 0)
        quote_cell.width = Cm(14)
        self._set_cell_background(quote_cell, self.colors['neutral_50'])
        self._set_cell_margins(quote_cell, Pt(20), Pt(10), Pt(24), Pt(24))
        
        quote_para = quote_cell.paragraphs[0]
        
        # Guillemets ouvrants
        quote_para.add_run("«").font.color.rgb = self.colors['accent']
        quote_para.add_run(f" {testimonial['quote']} ")
        quote_para.add_run("»").font.color.rgb = self.colors['accent']
        
        # Étoiles si rating fourni
        if "rating" in testimonial:
            stars = "⭐" * int(testimonial.get("rating", "5"))
            quote_para.add_run(f"\n{stars}")
        
        # Auteur
        author_cell = test_table.cell(1, 0)
        self._set_cell_background(author_cell, self.colors['primary'])
        self._set_cell_margins(author_cell, Pt(10), Pt(16), Pt(24), Pt(24))
        
        author_para = author_cell.paragraphs[0]
        author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        author_run = author_para.add_run(testimonial['author'])
        author_run.font.size = Pt(11)
        author_run.font.bold = True
        author_run.font.color.rgb = self.colors['white']
        
        if "company" in testimonial:
            company_run = author_para.add_run(f"\n{testimonial['company']}")
            company_run.font.size = Pt(9)
            company_run.font.color.rgb = self.colors['primary_light']
        
        doc.add_paragraph()
    
    def _create_process_step_number(self, cell, number: str) -> None:
        """Crée le numéro d'étape de processus"""
        
        cell.width = Cm(2)
        self._set_cell_background(cell, self.colors['primary'])
        self._set_cell_margins(cell, Pt(16), Pt(16), Pt(16), Pt(16))
        
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        run = para.add_run(number)
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = self.colors['white']
    
    def _create_process_step_description(self, cell, title: str, description: str) -> None:
        """Crée la description d'étape de processus"""
        
        self._set_cell_background(cell, self.colors['neutral_50'])
        self._set_cell_margins(cell, Pt(12), Pt(12), Pt(16), Pt(16))
        
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Titre
        title_run = para.add_run(f"{title}\n")
        title_run.font.size = Pt(12)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['primary']
        
        # Description
        desc_run = para.add_run(description)
        desc_run.font.size = Pt(9)
        desc_run.font.color.rgb = self.colors['neutral_600']
    
    def _create_process_arrow(self, cell) -> None:
        """Crée une flèche de processus"""
        
        cell.width = Cm(1)
        
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        arrow_run = para.add_run("➤")
        arrow_run.font.size = Pt(20)
        arrow_run.font.color.rgb = self.colors['accent']
    
    def _create_guarantee_badge(self, cell, guarantee: Dict[str, str]) -> None:
        """Crée un badge de garantie"""
        
        cell.width = Cm(5)
        self._set_cell_background(cell, self.colors['success'])
        self._add_cell_border(cell, self.colors['white'])
        self._set_cell_margins(cell, Pt(16), Pt(16), Pt(12), Pt(12))
        
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Icône
        icon_run = para.add_run(f"{guarantee['icon']}\n")
        icon_run.font.size = Pt(20)
        
        # Titre
        title_run = para.add_run(f"{guarantee['title']}\n")
        title_run.font.size = Pt(11)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['white']
        
        # Description
        desc_run = para.add_run(guarantee['description'])
        desc_run.font.size = Pt(9)
        desc_run.font.color.rgb = RGBColor(240, 253, 244)  # Vert très clair
    
    # Méthodes utilitaires héritées
    def _set_cell_background(self, cell, color: RGBColor):
        """Hérite de ProfessionalTemplateEngine"""
        return self.template_engine._set_cell_background(cell, color)
    
    def _set_cell_margins(self, cell, top=None, bottom=None, left=None, right=None):
        """Hérite de ProfessionalTemplateEngine"""
        return self.template_engine._set_cell_margins(cell, top, bottom, left, right)
    
    def _add_cell_border(self, cell, color: RGBColor, bottom_only: bool = False):
        """Hérite de ProfessionalTemplateEngine"""
        return self.template_engine._add_cell_border(cell, color, bottom_only)