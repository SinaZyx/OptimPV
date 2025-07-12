"""
Moteur de Templates Professionnelles OptimPV - Ultra Design
Transforme les documents Word en véritables créations d'agence de design
"""

import io
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import traceback
import math

try:
    from docx import Document
    from docx.shared import Inches, RGBColor, Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.enum.dml import MSO_THEME_COLOR_INDEX
    from docx.oxml.shared import OxmlElement, qn
    from docx.oxml.ns import nsdecls
    from docx.oxml import parse_xml
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    # Créer des classes et constantes mock pour éviter NameError
    class Document:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé. Installez-le avec: pip install python-docx")
    
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
    WD_COLOR_INDEX = None
    WD_TABLE_ALIGNMENT = None
    WD_ALIGN_VERTICAL = None
    MSO_THEME_COLOR_INDEX = None
    OxmlElement = None
    qn = None
    nsdecls = None
    parse_xml = None


class ProfessionalTemplateEngine:
    """
    Moteur de génération de templates Word ultra-professionnelles
    Niveau de qualité : Agence de design premium
    """
    
    def __init__(self):
        """Initialise le moteur avec la palette de couleurs premium OptimPV"""
        
        # 🎨 PALETTE COULEURS PREMIUM OPTIMPV
        self.colors = {
            # Couleurs principales OptimPV
            'primary': RGBColor(39, 174, 96),           # Vert OptimPV signature
            'primary_light': RGBColor(46, 204, 113),    # Vert clair
            'primary_dark': RGBColor(27, 135, 75),      # Vert foncé
            'primary_ultra_light': RGBColor(212, 245, 224),  # Vert très clair
            
            # Couleurs secondaires
            'secondary': RGBColor(52, 152, 219),        # Bleu énergie
            'secondary_light': RGBColor(93, 173, 226),  # Bleu clair
            'secondary_dark': RGBColor(40, 116, 166),   # Bleu foncé
            
            # Couleurs d'accent
            'accent': RGBColor(243, 156, 18),           # Orange solaire
            'accent_light': RGBColor(248, 196, 113),    # Orange clair
            'accent_dark': RGBColor(198, 126, 14),      # Orange foncé
            
            # Palette neutre sophistiquée
            'neutral_50': RGBColor(249, 250, 251),      # Blanc cassé
            'neutral_100': RGBColor(243, 244, 246),     # Gris très clair
            'neutral_200': RGBColor(229, 231, 235),     # Gris clair
            'neutral_300': RGBColor(209, 213, 219),     # Gris moyen clair
            'neutral_400': RGBColor(156, 163, 175),     # Gris moyen
            'neutral_500': RGBColor(107, 114, 128),     # Gris
            'neutral_600': RGBColor(75, 85, 99),        # Gris foncé
            'neutral_700': RGBColor(55, 65, 81),        # Gris très foncé
            'neutral_800': RGBColor(31, 41, 55),        # Presque noir
            'neutral_900': RGBColor(17, 24, 39),        # Noir profond
            
            # Couleurs sémantiques
            'success': RGBColor(34, 197, 94),           # Vert succès
            'warning': RGBColor(251, 146, 60),          # Orange warning
            'danger': RGBColor(239, 68, 68),            # Rouge danger
            'info': RGBColor(59, 130, 246),             # Bleu info
            
            # Couleurs spéciales
            'gold': RGBColor(255, 215, 0),              # Or premium
            'white': RGBColor(255, 255, 255),           # Blanc pur
            'black': RGBColor(0, 0, 0),                 # Noir pur
        }
        
        # 📝 SYSTÈME TYPOGRAPHIQUE MODULAIRE
        self.typography = {
            'hero_title': {'size': Pt(36), 'bold': True, 'color': 'white'},
            'page_title': {'size': Pt(24), 'bold': True, 'color': 'neutral_800'},
            'section_title': {'size': Pt(18), 'bold': True, 'color': 'primary'},
            'subsection_title': {'size': Pt(14), 'bold': True, 'color': 'neutral_700'},
            'body_large': {'size': Pt(12), 'bold': False, 'color': 'neutral_700'},
            'body': {'size': Pt(11), 'bold': False, 'color': 'neutral_600'},
            'body_small': {'size': Pt(10), 'bold': False, 'color': 'neutral_500'},
            'caption': {'size': Pt(9), 'bold': False, 'color': 'neutral_400'},
            'highlight': {'size': Pt(12), 'bold': True, 'color': 'accent'},
            'cta': {'size': Pt(14), 'bold': True, 'color': 'white'},
        }
        
        # 📐 SYSTÈME DE MISE EN PAGE
        self.layout = {
            'page_margin': Cm(2.5),
            'section_spacing': Pt(24),
            'paragraph_spacing': Pt(12),
            'line_height': 1.5,
            'column_gap': Cm(1),
        }
        
        # ✨ ÉLÉMENTS DÉCORATIFS UNICODE
        self.decorative = {
            'triangles': ['◤', '◥', '◣', '◢'],
            'circles': ['●', '○', '◐', '◑', '◒', '◓'],
            'arrows': ['➤', '➜', '➡', '⟶', '⇒'],
            'lines': ['━', '═', '─', '⸺'],
            'bullets': ['•', '◦', '▪', '▫', '⬥', '⬧'],
            'stars': ['★', '☆', '✦', '✧', '✩'],
            'shapes': ['▲', '▼', '◆', '◇', '■', '□'],
        }
    
    def create_premium_document(self, template_type: str = "executive") -> Document:
        """
        Crée un nouveau document avec template premium pré-configuré
        
        Args:
            template_type: Type de template ('executive', 'sales', 'technical')
            
        Returns:
            Document Word configuré avec styles premium
        """
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx non disponible")
        
        doc = Document()
        
        # Configuration de base premium
        self._setup_premium_styles(doc)
        self._setup_page_layout(doc)
        
        return doc
    
    def _setup_premium_styles(self, doc: Document):
        """Configure les styles premium pour le document"""
        
        styles = doc.styles
        
        # Style Hero Title (pour page de garde)
        if 'Hero Title' not in [s.name for s in styles]:
            hero_style = styles.add_style('Hero Title', 1)  # 1 = PARAGRAPH
            hero_font = hero_style.font
            hero_font.name = 'Calibri'
            hero_font.size = self.typography['hero_title']['size']
            hero_font.bold = self.typography['hero_title']['bold']
            hero_font.color.rgb = self.colors['white']
            hero_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Style Section Premium
        if 'Section Premium' not in [s.name for s in styles]:
            section_style = styles.add_style('Section Premium', 1)
            section_font = section_style.font
            section_font.name = 'Calibri'
            section_font.size = self.typography['section_title']['size']
            section_font.bold = self.typography['section_title']['bold']
            section_font.color.rgb = self.colors['primary']
            section_style.paragraph_format.space_before = self.layout['section_spacing']
            section_style.paragraph_format.space_after = Pt(12)
        
        # Style Body Premium
        if 'Body Premium' not in [s.name for s in styles]:
            body_style = styles.add_style('Body Premium', 1)
            body_font = body_style.font
            body_font.name = 'Calibri'
            body_font.size = self.typography['body']['size']
            body_font.color.rgb = self.colors['neutral_600']
            body_style.paragraph_format.line_spacing = self.layout['line_height']
            body_style.paragraph_format.space_after = self.layout['paragraph_spacing']
        
        # Style Highlight Premium
        if 'Highlight Premium' not in [s.name for s in styles]:
            highlight_style = styles.add_style('Highlight Premium', 1)
            highlight_font = highlight_style.font
            highlight_font.name = 'Calibri'
            highlight_font.size = self.typography['highlight']['size']
            highlight_font.bold = self.typography['highlight']['bold']
            highlight_font.color.rgb = self.colors['accent']
    
    def _setup_page_layout(self, doc: Document):
        """Configure la mise en page premium"""
        
        sections = doc.sections
        for section in sections:
            # Marges optimisées
            section.top_margin = self.layout['page_margin']
            section.bottom_margin = self.layout['page_margin']
            section.left_margin = self.layout['page_margin']
            section.right_margin = self.layout['page_margin']
    
    def create_premium_cover_page(self, doc: Document, title: str, subtitle: str, 
                                 client_name: str = None, project_name: str = None) -> None:
        """
        Crée une page de garde premium avec design immersif
        
        Design: Grande zone colorée avec titre, sous-titre et infos client
        """
        
        # 🎨 ZONE HERO COLORÉE (40% de la page)
        hero_table = doc.add_table(rows=1, cols=1)
        hero_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hero_cell = hero_table.cell(0, 0)
        
        # Configuration de la cellule hero
        hero_cell.width = Cm(18)
        self._set_cell_background(hero_cell, self.colors['primary'])
        self._set_cell_margins(hero_cell, top=Cm(3), bottom=Cm(3), left=Cm(2), right=Cm(2))
        
        # Titre principal
        hero_para = hero_cell.paragraphs[0]
        hero_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hero_run = hero_para.add_run(title)
        hero_run.font.size = Pt(32)
        hero_run.font.bold = True
        hero_run.font.color.rgb = self.colors['white']
        hero_run.font.name = 'Calibri'
        
        # Sous-titre
        subtitle_para = hero_cell.add_paragraph()
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_run = subtitle_para.add_run(subtitle)
        subtitle_run.font.size = Pt(16)
        subtitle_run.font.color.rgb = self.colors['primary_ultra_light']
        subtitle_run.font.name = 'Calibri'
        
        # Élément décoratif
        deco_para = hero_cell.add_paragraph()
        deco_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        deco_run = deco_para.add_run('◆ ◇ ◆')
        deco_run.font.size = Pt(20)
        deco_run.font.color.rgb = self.colors['accent']
        
        # 📋 INFORMATIONS CLIENT (zone blanche élégante)
        doc.add_paragraph()  # Espacement
        
        if client_name or project_name:
            info_table = doc.add_table(rows=1, cols=1)
            info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            info_cell = info_table.cell(0, 0)
            
            # Style de la zone info
            info_cell.width = Cm(12)
            self._set_cell_background(info_cell, self.colors['neutral_50'])
            self._add_cell_border(info_cell, self.colors['neutral_200'])
            self._set_cell_margins(info_cell, top=Cm(1.5), bottom=Cm(1.5), left=Cm(2), right=Cm(2))
            
            # Contenu client
            if client_name:
                client_para = info_cell.paragraphs[0]
                client_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                client_label = client_para.add_run('CLIENT\n')
                client_label.font.size = Pt(10)
                client_label.font.bold = True
                client_label.font.color.rgb = self.colors['neutral_400']
                client_value = client_para.add_run(client_name)
                client_value.font.size = Pt(16)
                client_value.font.bold = True
                client_value.font.color.rgb = self.colors['neutral_800']
            
            if project_name:
                project_para = info_cell.add_paragraph()
                project_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                project_label = project_para.add_run('PROJET\n')
                project_label.font.size = Pt(10)
                project_label.font.bold = True
                project_label.font.color.rgb = self.colors['neutral_400']
                project_value = project_para.add_run(project_name)
                project_value.font.size = Pt(16)
                project_value.font.bold = True
                project_value.font.color.rgb = self.colors['neutral_800']
        
        # 📅 DATE ET ENTREPRISE (bas de page)
        doc.add_paragraph()
        doc.add_paragraph()
        
        footer_para = doc.add_paragraph()
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        date_run = footer_para.add_run(f"Proposition établie le {datetime.now().strftime('%d/%m/%Y')}")
        date_run.font.size = Pt(11)
        date_run.font.color.rgb = self.colors['neutral_500']
        
        footer_para.add_run('\n')
        
        company_run = footer_para.add_run('🌱 OptimPV - Expert en Autoconsommation Collective')
        company_run.font.size = Pt(12)
        company_run.font.bold = True
        company_run.font.color.rgb = self.colors['primary']
        
        # Saut de page
        doc.add_page_break()
    
    def create_section_header(self, doc: Document, section_number: str, 
                            section_title: str, icon: str = "●") -> None:
        """
        Crée un en-tête de section avec bannière colorée design
        
        Design: Bannière pleine largeur avec numéro, titre et décoration
        """
        
        # 🎨 BANNIÈRE DE SECTION
        section_table = doc.add_table(rows=1, cols=3)
        section_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        
        # Configuration du tableau
        for cell in section_table.rows[0].cells:
            self._set_cell_background(cell, self.colors['primary'])
            self._set_cell_margins(cell, top=Pt(12), bottom=Pt(12), left=Pt(16), right=Pt(16))
        
        # Cellule numéro (cercle)
        number_cell = section_table.cell(0, 0)
        number_cell.width = Cm(2)
        number_para = number_cell.paragraphs[0]
        number_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        number_run = number_para.add_run(section_number)
        number_run.font.size = Pt(16)
        number_run.font.bold = True
        number_run.font.color.rgb = self.colors['white']
        
        # Cellule titre
        title_cell = section_table.cell(0, 1)
        title_cell.width = Cm(12)
        title_para = title_cell.paragraphs[0]
        title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        title_run = title_para.add_run(f"{icon} {section_title}")
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['white']
        
        # Cellule décorative
        deco_cell = section_table.cell(0, 2)
        deco_cell.width = Cm(2)
        deco_para = deco_cell.paragraphs[0]
        deco_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        deco_run = deco_para.add_run('◆')
        deco_run.font.size = Pt(16)
        deco_run.font.color.rgb = self.colors['accent']
        
        # Espacement après
        doc.add_paragraph()
    
    def create_info_box(self, doc: Document, content: str, box_type: str = 'info', 
                       title: str = None) -> None:
        """
        Crée un encadré d'information design avec couleurs et styles
        
        Types: 'info', 'success', 'warning', 'danger', 'highlight'
        """
        
        # Configuration par type
        type_config = {
            'info': {'color': self.colors['info'], 'bg': self.colors['neutral_50'], 'icon': 'ℹ'},
            'success': {'color': self.colors['success'], 'bg': RGBColor(240, 253, 244), 'icon': '✓'},
            'warning': {'color': self.colors['warning'], 'bg': RGBColor(255, 251, 235), 'icon': '⚠'},
            'danger': {'color': self.colors['danger'], 'bg': RGBColor(254, 242, 242), 'icon': '⚠'},
            'highlight': {'color': self.colors['accent'], 'bg': self.colors['neutral_50'], 'icon': '★'},
        }
        
        config = type_config.get(box_type, type_config['info'])
        
        # 📦 ENCADRÉ PRINCIPAL
        box_table = doc.add_table(rows=1, cols=2)
        box_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        
        # Cellule icône/couleur
        icon_cell = box_table.cell(0, 0)
        icon_cell.width = Cm(1)
        self._set_cell_background(icon_cell, config['color'])
        self._set_cell_margins(icon_cell, top=Pt(12), bottom=Pt(12), left=Pt(8), right=Pt(8))
        
        icon_para = icon_cell.paragraphs[0]
        icon_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        icon_run = icon_para.add_run(config['icon'])
        icon_run.font.size = Pt(16)
        icon_run.font.bold = True
        icon_run.font.color.rgb = self.colors['white']
        
        # Cellule contenu
        content_cell = box_table.cell(0, 1)
        self._set_cell_background(content_cell, config['bg'])
        self._set_cell_margins(content_cell, top=Pt(12), bottom=Pt(12), left=Pt(16), right=Pt(16))
        
        content_para = content_cell.paragraphs[0]
        
        # Titre optionnel
        if title:
            title_run = content_para.add_run(f"{title}\n")
            title_run.font.size = Pt(12)
            title_run.font.bold = True
            title_run.font.color.rgb = config['color']
        
        # Contenu
        content_run = content_para.add_run(content)
        content_run.font.size = Pt(11)
        content_run.font.color.rgb = self.colors['neutral_700']
        
        # Espacement après
        doc.add_paragraph()
    
    def create_professional_table(self, doc: Document, data: List[List[str]], 
                                headers: List[str] = None, style: str = 'modern') -> None:
        """
        Crée un tableau professionnel avec design avancé
        
        Styles: 'modern', 'minimal', 'accent', 'dashboard'
        """
        
        rows = len(data)
        cols = len(data[0]) if data else len(headers) if headers else 2
        
        # Ajout d'une ligne pour les en-têtes si fournis
        if headers:
            rows += 1
        
        table = doc.add_table(rows=rows, cols=cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # ⭐ STYLE MODERN
        if style == 'modern':
            self._apply_modern_table_style(table, data, headers)
        
        # ⭐ STYLE MINIMAL
        elif style == 'minimal':
            self._apply_minimal_table_style(table, data, headers)
        
        # ⭐ STYLE ACCENT
        elif style == 'accent':
            self._apply_accent_table_style(table, data, headers)
        
        # ⭐ STYLE DASHBOARD
        elif style == 'dashboard':
            self._apply_dashboard_table_style(table, data, headers)
        
        # Espacement après
        doc.add_paragraph()
    
    def _apply_modern_table_style(self, table, data: List[List[str]], headers: List[str] = None):
        """Applique le style moderne au tableau"""
        
        row_idx = 0
        
        # En-têtes colorés
        if headers:
            header_row = table.rows[0]
            for i, header in enumerate(headers):
                cell = header_row.cells[i]
                self._set_cell_background(cell, self.colors['primary'])
                self._set_cell_margins(cell, top=Pt(12), bottom=Pt(12), left=Pt(16), right=Pt(16))
                
                para = cell.paragraphs[0]
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = para.add_run(header)
                run.font.size = Pt(11)
                run.font.bold = True
                run.font.color.rgb = self.colors['white']
            
            row_idx = 1
        
        # Données avec lignes alternées
        for i, row_data in enumerate(data):
            row = table.rows[row_idx + i]
            
            # Couleur de fond alternée
            bg_color = self.colors['neutral_50'] if i % 2 == 0 else self.colors['white']
            
            for j, cell_data in enumerate(row_data):
                cell = row.cells[j]
                self._set_cell_background(cell, bg_color)
                self._set_cell_margins(cell, top=Pt(8), bottom=Pt(8), left=Pt(16), right=Pt(16))
                
                para = cell.paragraphs[0]
                run = para.add_run(str(cell_data))
                run.font.size = Pt(10)
                run.font.color.rgb = self.colors['neutral_700']
    
    def _apply_minimal_table_style(self, table, data: List[List[str]], headers: List[str] = None):
        """Applique le style minimal au tableau"""
        
        row_idx = 0
        
        # En-têtes épurés
        if headers:
            header_row = table.rows[0]
            for i, header in enumerate(headers):
                cell = header_row.cells[i]
                self._add_cell_border(cell, self.colors['neutral_300'], bottom_only=True)
                self._set_cell_margins(cell, top=Pt(16), bottom=Pt(16), left=Pt(24), right=Pt(24))
                
                para = cell.paragraphs[0]
                run = para.add_run(header)
                run.font.size = Pt(11)
                run.font.bold = True
                run.font.color.rgb = self.colors['neutral_800']
            
            row_idx = 1
        
        # Données épurées
        for i, row_data in enumerate(data):
            row = table.rows[row_idx + i]
            
            for j, cell_data in enumerate(row_data):
                cell = row.cells[j]
                self._set_cell_margins(cell, top=Pt(12), bottom=Pt(12), left=Pt(24), right=Pt(24))
                
                para = cell.paragraphs[0]
                run = para.add_run(str(cell_data))
                run.font.size = Pt(10)
                run.font.color.rgb = self.colors['neutral_600']
    
    def _apply_accent_table_style(self, table, data: List[List[str]], headers: List[str] = None):
        """Applique le style avec première colonne accentuée"""
        
        row_idx = 0
        
        # En-têtes
        if headers:
            header_row = table.rows[0]
            for i, header in enumerate(headers):
                cell = header_row.cells[i]
                bg_color = self.colors['accent'] if i == 0 else self.colors['neutral_100']
                text_color = self.colors['white'] if i == 0 else self.colors['neutral_800']
                
                self._set_cell_background(cell, bg_color)
                self._set_cell_margins(cell, top=Pt(12), bottom=Pt(12), left=Pt(16), right=Pt(16))
                
                para = cell.paragraphs[0]
                run = para.add_run(header)
                run.font.size = Pt(11)
                run.font.bold = True
                run.font.color.rgb = text_color
            
            row_idx = 1
        
        # Données avec première colonne accentuée
        for i, row_data in enumerate(data):
            row = table.rows[row_idx + i]
            
            for j, cell_data in enumerate(row_data):
                cell = row.cells[j]
                
                if j == 0:  # Première colonne
                    self._set_cell_background(cell, self.colors['accent_light'])
                    text_color = self.colors['neutral_800']
                    font_bold = True
                else:
                    self._set_cell_background(cell, self.colors['white'])
                    text_color = self.colors['neutral_600']
                    font_bold = False
                
                self._set_cell_margins(cell, top=Pt(8), bottom=Pt(8), left=Pt(16), right=Pt(16))
                
                para = cell.paragraphs[0]
                run = para.add_run(str(cell_data))
                run.font.size = Pt(10)
                run.font.bold = font_bold
                run.font.color.rgb = text_color
    
    def _apply_dashboard_table_style(self, table, data: List[List[str]], headers: List[str] = None):
        """Applique le style dashboard avec grandes cellules"""
        
        row_idx = 0
        
        # En-têtes dashboard
        if headers:
            header_row = table.rows[0]
            for i, header in enumerate(headers):
                cell = header_row.cells[i]
                self._set_cell_background(cell, self.colors['primary_dark'])
                self._set_cell_margins(cell, top=Pt(20), bottom=Pt(20), left=Pt(24), right=Pt(24))
                
                para = cell.paragraphs[0]
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = para.add_run(header)
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = self.colors['white']
            
            row_idx = 1
        
        # Données dashboard (grandes cellules)
        for i, row_data in enumerate(data):
            row = table.rows[row_idx + i]
            
            for j, cell_data in enumerate(row_data):
                cell = row.cells[j]
                self._set_cell_background(cell, self.colors['neutral_50'])
                self._set_cell_margins(cell, top=Pt(20), bottom=Pt(20), left=Pt(24), right=Pt(24))
                
                para = cell.paragraphs[0]
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = para.add_run(str(cell_data))
                run.font.size = Pt(14)
                run.font.bold = True
                run.font.color.rgb = self.colors['primary']
    
    # ===============================
    # MÉTHODES UTILITAIRES AVANCÉES
    # ===============================
    
    def _extract_rgb_from_color(self, color: RGBColor) -> tuple:
        """Extrait les composantes RGB d'un objet RGBColor de manière compatible"""
        try:
            # Méthode 1: Accès direct (versions récentes)
            if hasattr(color, 'rgb'):
                return color.rgb
            elif hasattr(color, 'r') and hasattr(color, 'g') and hasattr(color, 'b'):
                return (color.r, color.g, color.b)
            # Méthode 2: Depuis _color_val (versions plus anciennes)
            elif hasattr(color, '_color_val'):
                val = color._color_val
                r = (val >> 16) & 0xFF
                g = (val >> 8) & 0xFF
                b = val & 0xFF
                return (r, g, b)
            else:
                # Fallback couleur OptimPV par défaut
                return (39, 174, 96)
        except (AttributeError, TypeError):
            # Fallback ultime
            return (39, 174, 96)
    
    def _color_to_hex(self, color: RGBColor) -> str:
        """Convertit un RGBColor en string hexadécimale"""
        try:
            r, g, b = self._extract_rgb_from_color(color)
            return f"{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "27ae60"  # Vert OptimPV par défaut
    
    def _set_cell_background(self, cell, color: RGBColor):
        """Définit la couleur de fond d'une cellule"""
        try:
            # Utiliser la méthode centralisée pour extraire la couleur
            color_hex = self._color_to_hex(color)
            
            # Configuration XML pour la couleur de fond
            cell._tc.get_or_add_tcPr().append(
                parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
            )
        except Exception as e:
            # Fallback silencieux en cas d'erreur
            pass
    
    def _set_cell_margins(self, cell, top=None, bottom=None, left=None, right=None):
        """Définit les marges d'une cellule"""
        try:
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = tcPr.find(qn('w:tcMar'))
            
            if tcMar is None:
                tcMar = OxmlElement('w:tcMar')
                tcPr.append(tcMar)
            
            # Conversion Pt vers twips (1 pt = 20 twips)
            if top:
                top_elem = tcMar.find(qn('w:top')) or OxmlElement('w:top')
                top_elem.set(qn('w:w'), str(int(top.pt * 20)))
                top_elem.set(qn('w:type'), 'dxa')
                if top_elem not in tcMar:
                    tcMar.append(top_elem)
            
            if bottom:
                bottom_elem = tcMar.find(qn('w:bottom')) or OxmlElement('w:bottom')
                bottom_elem.set(qn('w:w'), str(int(bottom.pt * 20)))
                bottom_elem.set(qn('w:type'), 'dxa')
                if bottom_elem not in tcMar:
                    tcMar.append(bottom_elem)
            
            if left:
                left_elem = tcMar.find(qn('w:left')) or OxmlElement('w:left')
                left_elem.set(qn('w:w'), str(int(left.pt * 20)))
                left_elem.set(qn('w:type'), 'dxa')
                if left_elem not in tcMar:
                    tcMar.append(left_elem)
            
            if right:
                right_elem = tcMar.find(qn('w:right')) or OxmlElement('w:right')
                right_elem.set(qn('w:w'), str(int(right.pt * 20)))
                right_elem.set(qn('w:type'), 'dxa')
                if right_elem not in tcMar:
                    tcMar.append(right_elem)
                    
        except Exception as e:
            # Fallback silencieux
            pass
    
    def _add_cell_border(self, cell, color: RGBColor, bottom_only: bool = False):
        """Ajoute une bordure à une cellule"""
        try:
            # Utiliser la méthode centralisée pour extraire la couleur
            color_hex = self._color_to_hex(color)
            
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = tcPr.find(qn('w:tcBorders'))
            
            if tcBorders is None:
                tcBorders = OxmlElement('w:tcBorders')
                tcPr.append(tcBorders)
            
            # Bordure du bas (toujours)
            bottom_border = OxmlElement('w:bottom')
            bottom_border.set(qn('w:val'), 'single')
            bottom_border.set(qn('w:sz'), '4')  # Épaisseur
            bottom_border.set(qn('w:color'), color_hex)
            tcBorders.append(bottom_border)
            
            if not bottom_only:
                # Bordures complètes
                for side in ['top', 'left', 'right']:
                    border = OxmlElement(f'w:{side}')
                    border.set(qn('w:val'), 'single')
                    border.set(qn('w:sz'), '4')
                    border.set(qn('w:color'), color_hex)
                    tcBorders.append(border)
                    
        except Exception as e:
            pass
    
    def create_gradient_effect(self, doc: Document, color1: RGBColor, color2: RGBColor, 
                             steps: int = 10, height: Cm = Cm(1)) -> None:
        """
        Simule un effet de gradient avec des cellules de tableau
        Version robuste avec fallback en cas d'erreur
        """
        
        try:
            gradient_table = doc.add_table(rows=1, cols=steps)
            gradient_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            for i in range(steps):
                # Calcul de la couleur intermédiaire
                ratio = i / (steps - 1)
                
                try:
                    # Utiliser la méthode centralisée pour extraire les couleurs
                    r1, g1, b1 = self._extract_rgb_from_color(color1)
                    r2, g2, b2 = self._extract_rgb_from_color(color2)
                    
                    r = int(r1 * (1 - ratio) + r2 * ratio)
                    g = int(g1 * (1 - ratio) + g2 * ratio)
                    b = int(b1 * (1 - ratio) + b2 * ratio)
                    
                    intermediate_color = RGBColor(r, g, b)
                    
                except Exception:
                    # Fallback: utiliser directement une des deux couleurs
                    intermediate_color = color1 if ratio < 0.5 else color2
                
                # Application à la cellule
                cell = gradient_table.cell(0, i)
                cell.width = Cm(18 / steps)  # Largeur uniforme
                self._set_cell_background(cell, intermediate_color)
                self._set_cell_margins(cell, top=height/2, bottom=height/2)
                
                # Cellule vide pour l'effet visuel
                cell.paragraphs[0].add_run(' ')
            
            doc.add_paragraph()  # Espacement
            
        except Exception as e:
            # Fallback ultime: créer un simple séparateur coloré
            print(f"⚠️ Gradient non supporté, utilisation d'un séparateur simple: {e}")
            self.add_decorative_separator(doc, 'line')
    
    def add_decorative_separator(self, doc: Document, style: str = 'diamond') -> None:
        """
        Ajoute un séparateur décoratif entre les sections
        
        Styles: 'diamond', 'line', 'dots', 'stars'
        """
        
        separators = {
            'diamond': '◆ ◇ ◆ ◇ ◆',
            'line': '━━━━━━━━━━━━━━━━━━━━',
            'dots': '• • • • • • • • •',
            'stars': '★ ☆ ★ ☆ ★',
            'modern': '▬▬▬ ◆ ▬▬▬',
        }
        
        separator_text = separators.get(style, separators['diamond'])
        
        sep_para = doc.add_paragraph()
        sep_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sep_run = sep_para.add_run(separator_text)
        sep_run.font.size = Pt(14)
        sep_run.font.color.rgb = self.colors['accent']
        
        doc.add_paragraph()  # Espacement après
    
    def create_call_to_action_box(self, doc: Document, cta_text: str, 
                                 button_text: str = "Contactez-nous") -> None:
        """
        Crée un encadré call-to-action premium
        """
        
        # Table principale CTA
        cta_table = doc.add_table(rows=3, cols=1)
        cta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # En-tête coloré
        header_cell = cta_table.cell(0, 0)
        header_cell.width = Cm(14)
        self._set_cell_background(header_cell, self.colors['accent'])
        self._set_cell_margins(header_cell, top=Pt(16), bottom=Pt(16), left=Pt(24), right=Pt(24))
        
        header_para = header_cell.paragraphs[0]
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_run = header_para.add_run('🚀 PASSEZ À L\'ACTION')
        header_run.font.size = Pt(16)
        header_run.font.bold = True
        header_run.font.color.rgb = self.colors['white']
        
        # Contenu CTA
        content_cell = cta_table.cell(1, 0)
        self._set_cell_background(content_cell, self.colors['neutral_50'])
        self._set_cell_margins(content_cell, top=Pt(20), bottom=Pt(20), left=Pt(24), right=Pt(24))
        
        content_para = content_cell.paragraphs[0]
        content_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        content_run = content_para.add_run(cta_text)
        content_run.font.size = Pt(12)
        content_run.font.color.rgb = self.colors['neutral_700']
        
        # Bouton d'action
        button_cell = cta_table.cell(2, 0)
        self._set_cell_background(button_cell, self.colors['primary'])
        self._set_cell_margins(button_cell, top=Pt(16), bottom=Pt(16), left=Pt(24), right=Pt(24))
        
        button_para = button_cell.paragraphs[0]
        button_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        button_run = button_para.add_run(f'📞 {button_text}')
        button_run.font.size = Pt(14)
        button_run.font.bold = True
        button_run.font.color.rgb = self.colors['white']
        
        doc.add_paragraph()  # Espacement