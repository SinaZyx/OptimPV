"""
Module pour les fonctionnalités d'export (PDF, PNG, Excel)
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import io
import base64
from datetime import datetime
import tempfile
import os

# Import optionnel pour PDF
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def export_chart_to_png(fig: go.Figure, filename: str = "chart.png", width: int = 1200, height: int = 800) -> bytes:
    """
    Exporte un graphique Plotly en PNG
    """
    try:
        # Convertir en bytes
        img_bytes = fig.to_image(format="png", width=width, height=height)
        return img_bytes
    except Exception as e:
        st.error(f"Erreur lors de l'export PNG: {e}")
        return None

def export_chart_to_svg(fig: go.Figure, filename: str = "chart.svg") -> str:
    """
    Exporte un graphique Plotly en SVG
    """
    try:
        return fig.to_image(format="svg").decode()
    except Exception as e:
        st.error(f"Erreur lors de l'export SVG: {e}")
        return None

def export_data_to_excel(data_dict: Dict[str, pd.DataFrame], filename: str = "export.xlsx") -> bytes:
    """
    Exporte plusieurs DataFrames vers un fichier Excel avec plusieurs onglets
    """
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BD',
                'border': 1
            })
            
            currency_format = workbook.add_format({'num_format': '#,##0.00 €'})
            percent_format = workbook.add_format({'num_format': '0.00%'})
            
            # Exporter chaque DataFrame
            for sheet_name, df in data_dict.items():
                # Limiter le nom de l'onglet à 31 caractères (limite Excel)
                sheet_name = sheet_name[:31]
                
                df.to_excel(writer, sheet_name=sheet_name, index=True)
                worksheet = writer.sheets[sheet_name]
                
                # Appliquer les formats
                for idx, col in enumerate(df.columns):
                    if 'prix' in col.lower() or '€' in str(col) or 'montant' in col.lower():
                        worksheet.set_column(idx + 1, idx + 1, 15, currency_format)
                    elif '%' in str(col) or 'taux' in col.lower():
                        worksheet.set_column(idx + 1, idx + 1, 12, percent_format)
                    else:
                        worksheet.set_column(idx + 1, idx + 1, 15)
                
                # Format des en-têtes
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num + 1, value, header_format)
        
        output.seek(0)
        return output.read()
        
    except Exception as e:
        st.error(f"Erreur lors de l'export Excel: {e}")
        return None

def create_pdf_report(
    results_data: Dict[str, Any],
    config: Dict[str, Any],
    charts: List[go.Figure],
    report_type: str = "client",
    filename: str = "rapport.pdf"
) -> Optional[bytes]:
    """
    Crée un rapport PDF complet
    """
    if not REPORTLAB_AVAILABLE:
        st.error("ReportLab n'est pas installé. Installez-le avec: pip install reportlab")
        return None
    
    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_filename = tmp_file.name
        
        # Configuration du document
        doc = SimpleDocTemplate(
            tmp_filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=1  # Centre
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12
        )
        
        # Contenu du rapport
        story = []
        
        # Page de titre
        if report_type == "client":
            story.append(Paragraph("Rapport d'Analyse Photovoltaïque", title_style))
            story.append(Paragraph("Synthèse Client", styles['Heading2']))
        else:
            story.append(Paragraph("Rapport Financier Photovoltaïque", title_style))
            story.append(Paragraph("Analyse Investisseur", styles['Heading2']))
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Paragraph(f"Scénario: {results_data.get('scenario_name', 'N/A')}", styles['Normal']))
        story.append(PageBreak())
        
        # Résumé exécutif
        story.append(Paragraph("Résumé Exécutif", heading_style))
        
        if report_type == "client":
            # Données client
            prix_optimal = results_data.get('prix_revente', 0)
            tarif_edf = config.get('tarif_edf_reference', 0.21)
            economie_pct = ((tarif_edf - prix_optimal) / tarif_edf * 100) if tarif_edf > 0 else 0
            
            summary_data = [
                ["Indicateur", "Valeur"],
                ["Prix optimal", f"{prix_optimal:.4f} €/kWh"],
                ["Économie vs EDF", f"{economie_pct:.1f}%"],
                ["Taux d'autoconsommation", f"{results_data.get('taux_autoconsommation', 0)*100:.1f}%"],
            ]
        else:
            # Données investisseur
            summary_data = [
                ["Indicateur", "Valeur"],
                ["VAN", f"{results_data.get('npv', 0):,.0f} €"],
                ["TRI", f"{results_data.get('irr', 0)*100:.1f}%"],
                ["Payback", f"{results_data.get('payback_period', 0):.1f} ans"],
                ["DSCR moyen", f"{results_data.get('avg_dscr', 0):.2f}"],
                ["LCOE", f"{results_data.get('lcoe', 0):.4f} €/kWh"],
            ]
        
        # Créer le tableau
        t = Table(summary_data, colWidths=[3*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(t)
        story.append(PageBreak())
        
        # Graphiques
        story.append(Paragraph("Analyses Graphiques", heading_style))
        
        # Convertir et ajouter les graphiques
        for i, fig in enumerate(charts[:6]):  # Limiter à 6 graphiques
            if fig:
                # Convertir en image
                img_bytes = export_chart_to_png(fig, width=600, height=400)
                if img_bytes:
                    # Sauvegarder temporairement
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as img_tmp:
                        img_tmp.write(img_bytes)
                        img_tmp_name = img_tmp.name
                    
                    # Ajouter l'image au PDF
                    img = Image(img_tmp_name, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                    
                    # Nettoyer
                    os.unlink(img_tmp_name)
                    
                    # Nouvelle page tous les 2 graphiques
                    if (i + 1) % 2 == 0:
                        story.append(PageBreak())
        
        # Générer le PDF
        doc.build(story)
        
        # Lire le fichier
        with open(tmp_filename, 'rb') as f:
            pdf_bytes = f.read()
        
        # Nettoyer
        os.unlink(tmp_filename)
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Erreur lors de la création du PDF: {e}")
        return None

def create_download_button(
    data: bytes,
    filename: str,
    file_type: str,
    button_text: str = "Télécharger"
) -> None:
    """
    Crée un bouton de téléchargement Streamlit
    """
    mime_types = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'svg': 'image/svg+xml',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv'
    }
    
    mime_type = mime_types.get(file_type, 'application/octet-stream')
    
    st.download_button(
        label=button_text,
        data=data,
        file_name=filename,
        mime=mime_type
    )

def display_export_interface(
    results_data: Dict[str, Any],
    config: Dict[str, Any],
    charts: Dict[str, go.Figure]
) -> None:
    """
    Interface d'export complète
    """
    st.markdown("### 📤 Options d'Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📄 Rapport PDF")
        report_type = st.radio(
            "Type de rapport",
            options=['client', 'investor'],
            format_func=lambda x: "Client" if x == 'client' else "Investisseur"
        )
        
        if st.button("Générer PDF", key="generate_pdf"):
            with st.spinner("Génération du rapport PDF..."):
                # Sélectionner les graphiques appropriés
                selected_charts = []
                for name, chart in charts.items():
                    if report_type == 'client' and 'client' in name.lower():
                        selected_charts.append(chart)
                    elif report_type == 'investor' and 'investor' not in name.lower():
                        selected_charts.append(chart)
                
                pdf_bytes = create_pdf_report(
                    results_data,
                    config,
                    selected_charts[:6],
                    report_type,
                    f"rapport_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
                )
                
                if pdf_bytes:
                    create_download_button(
                        pdf_bytes,
                        f"rapport_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        'pdf',
                        "📥 Télécharger le PDF"
                    )
    
    with col2:
        st.markdown("#### 🖼️ Export Images")
        chart_name = st.selectbox(
            "Graphique à exporter",
            options=list(charts.keys())
        )
        
        format_option = st.radio(
            "Format",
            options=['png', 'svg']
        )
        
        if st.button("Exporter l'image", key="export_image"):
            selected_chart = charts.get(chart_name)
            if selected_chart:
                if format_option == 'png':
                    img_bytes = export_chart_to_png(selected_chart)
                    if img_bytes:
                        create_download_button(
                            img_bytes,
                            f"{chart_name}_{datetime.now().strftime('%Y%m%d')}.png",
                            'png',
                            "📥 Télécharger PNG"
                        )
                else:
                    svg_str = export_chart_to_svg(selected_chart)
                    if svg_str:
                        create_download_button(
                            svg_str.encode(),
                            f"{chart_name}_{datetime.now().strftime('%Y%m%d')}.svg",
                            'svg',
                            "📥 Télécharger SVG"
                        )
    
    with col3:
        st.markdown("#### 📊 Export Données")
        
        # Préparer les données pour l'export
        export_data = {}
        
        if 'monthly_data' in results_data:
            export_data['Données_Mensuelles'] = results_data['monthly_data']
        
        # Résumé des indicateurs
        indicators_df = pd.DataFrame({
            'Indicateur': ['VAN', 'TRI', 'Payback', 'DSCR', 'LCOE'],
            'Valeur': [
                results_data.get('npv', 0),
                results_data.get('irr', 0) * 100,
                results_data.get('payback_period', 0),
                results_data.get('avg_dscr', 0),
                results_data.get('lcoe', 0)
            ],
            'Unité': ['€', '%', 'ans', '', '€/kWh']
        })
        export_data['Indicateurs'] = indicators_df
        
        if st.button("Exporter Excel", key="export_excel"):
            excel_bytes = export_data_to_excel(export_data)
            if excel_bytes:
                create_download_button(
                    excel_bytes,
                    f"donnees_optimpv_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    'xlsx',
                    "📥 Télécharger Excel"
                )

# Fonction pour l'optimisation des performances
@st.cache_data(ttl=3600)
def cached_chart_generation(chart_function, *args, **kwargs):
    """
    Cache les graphiques générés pour améliorer les performances
    """
    return chart_function(*args, **kwargs)

def optimize_dataframe_display(df: pd.DataFrame, max_rows: int = 1000) -> pd.DataFrame:
    """
    Optimise l'affichage des DataFrames volumineux
    """
    if len(df) > max_rows:
        st.warning(f"Affichage limité aux {max_rows} premières lignes pour les performances.")
        return df.head(max_rows)
    return df