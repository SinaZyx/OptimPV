#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Styles CSS personnalisés pour les tooltips interactifs.
"""

import streamlit as st

def inject_custom_css():
    """
    Injecte des styles CSS personnalisés pour améliorer l'interaction avec les tooltips.
    """
    css = """
    <style>
    /* Styles pour les tooltips PyDeck */
    .deck-tooltip {
        pointer-events: all !important;
        z-index: 999999 !important;
        position: fixed !important;
    }
    
    .deck-tooltip > div {
        pointer-events: all !important;
        cursor: default !important;
    }
    
    /* Amélioration de l'interaction avec les liens */
    .deck-tooltip a {
        pointer-events: all !important;
        cursor: pointer !important;
        position: relative !important;
        z-index: 1000000 !important;
    }
    
    .deck-tooltip button {
        pointer-events: all !important;
        cursor: pointer !important;
        position: relative !important;
        z-index: 1000000 !important;
    }
    
    /* Style pour le conteneur de tooltip personnalisé */
    .custom-tooltip-container {
        background-color: white;
        border: 2px solid #2c3e50;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        max-width: 350px;
        z-index: 999999;
        pointer-events: all;
    }
    
    /* Animation pour l'apparition du tooltip */
    @keyframes tooltipFadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .deck-tooltip {
        animation: tooltipFadeIn 0.2s ease-out;
    }
    
    /* Style pour les boutons d'action dans le tooltip */
    .tooltip-action-button {
        display: inline-block;
        padding: 8px 16px;
        margin: 4px;
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-weight: bold;
        transition: all 0.3s;
        cursor: pointer;
        pointer-events: all;
    }
    
    .tooltip-action-button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Fix pour la superposition avec la carte */
    .stDeckGlJsonChart {
        position: relative;
    }
    
    /* Amélioration de la visibilité du curseur */
    .mapboxgl-canvas {
        cursor: pointer !important;
    }
    
    /* Style pour le mode sélection */
    .deck-layer-polygon-layer {
        cursor: pointer !important;
    }
    
    /* Fix pour les événements de souris sur mobile */
    @media (max-width: 768px) {
        .deck-tooltip {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            max-width: 90vw !important;
        }
    }
    </style>
    """
    
    # JavaScript pour améliorer l'interaction
    js = """
    <script>
    // Fonction pour forcer l'interaction avec les tooltips
    function enableTooltipInteraction() {
        // Attendre que les tooltips soient rendus
        setTimeout(() => {
            const tooltips = document.querySelectorAll('.deck-tooltip');
            tooltips.forEach(tooltip => {
                tooltip.style.pointerEvents = 'all';
                tooltip.style.zIndex = '999999';
                
                // Empêcher la fermeture du tooltip au clic
                tooltip.addEventListener('click', (e) => {
                    e.stopPropagation();
                });
                
                // Gérer les liens dans le tooltip
                const links = tooltip.querySelectorAll('a');
                links.forEach(link => {
                    link.style.pointerEvents = 'all';
                    link.style.cursor = 'pointer';
                    link.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                });
                
                // Gérer les boutons dans le tooltip
                const buttons = tooltip.querySelectorAll('button');
                buttons.forEach(button => {
                    button.style.pointerEvents = 'all';
                    button.style.cursor = 'pointer';
                    button.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                });
            });
        }, 100);
    }
    
    // Observer les changements dans le DOM pour les nouveaux tooltips
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach((node) => {
                    if (node.classList && node.classList.contains('deck-tooltip')) {
                        enableTooltipInteraction();
                    }
                });
            }
        });
    });
    
    // Démarrer l'observation
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Activer l'interaction au chargement initial
    document.addEventListener('DOMContentLoaded', enableTooltipInteraction);
    
    // Réactiver périodiquement pour s'assurer que les tooltips restent interactifs
    setInterval(enableTooltipInteraction, 500);
    </script>
    """
    
    # Injecter CSS et JavaScript
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(js, unsafe_allow_html=True)