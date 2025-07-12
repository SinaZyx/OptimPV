/**
 * OptimPV - Proposition Commerciale Interactive
 * JavaScript pour animations, graphiques et interactions modernes
 */

class SolarProposalAnimations {
    constructor() {
        this.isLoaded = false;
        this.initializeAnimations();
    }

    initializeAnimations() {
        // Attendre que le DOM soit chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.setupScrollAnimations();
        this.setupCounterAnimations();
        this.setupFAQAccordion();
        this.setupHoverEffects();
        this.setupChartAnimations();
        this.isLoaded = true;
    }

    // Animation de compteur avec effet de décompte
    animateCounter(element, target, duration = 2000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const updateCounter = () => {
            current += increment;
            if (current >= target) {
                current = target;
                element.textContent = Math.floor(current).toLocaleString('fr-FR');
                return;
            }
            element.textContent = Math.floor(current).toLocaleString('fr-FR');
            requestAnimationFrame(updateCounter);
        };
        
        requestAnimationFrame(updateCounter);
    }

    // Animations au scroll avec Intersection Observer
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    
                    // Animer les compteurs
                    if (entry.target.classList.contains('counter')) {
                        const target = parseInt(entry.target.dataset.target);
                        this.animateCounter(entry.target, target);
                    }
                    
                    // Animer les éléments de timeline
                    if (entry.target.classList.contains('timeline-item')) {
                        setTimeout(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateX(0)';
                        }, Array.from(entry.target.parentNode.children).indexOf(entry.target) * 200);
                    }
                }
            });
        }, observerOptions);

        // Observer tous les éléments animables
        document.querySelectorAll('.chart-container, .timeline-item, .counter, .fade-in').forEach(el => {
            observer.observe(el);
        });
    }

    // Configuration de l'accordéon FAQ
    setupFAQAccordion() {
        document.querySelectorAll('.faq-question').forEach(question => {
            question.addEventListener('click', () => {
                const faqItem = question.parentNode;
                const isActive = faqItem.classList.contains('active');
                
                // Fermer tous les autres items
                document.querySelectorAll('.faq-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                // Ouvrir/fermer l'item cliqué
                if (!isActive) {
                    faqItem.classList.add('active');
                }
            });
        });
    }

    // Effets de hover avancés
    setupHoverEffects() {
        // Effet parallax sur les cartes métriques
        document.querySelectorAll('.cover-metric').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 10;
                const rotateY = (centerX - x) / 10;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(20px)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
            });
        });

        // Effet ripple sur les boutons
        document.querySelectorAll('.btn-modern').forEach(button => {
            button.addEventListener('click', (e) => {
                const rect = button.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const ripple = document.createElement('span');
                ripple.style.cssText = `
                    position: absolute;
                    width: 20px;
                    height: 20px;
                    background: rgba(255,255,255,0.6);
                    border-radius: 50%;
                    left: ${x - 10}px;
                    top: ${y - 10}px;
                    animation: ripple 0.6s ease-out;
                    pointer-events: none;
                `;
                
                button.appendChild(ripple);
                setTimeout(() => ripple.remove(), 600);
            });
        });
    }

    // Animations pour les graphiques (Compatible avec Chart.js et Plotly)
    setupChartAnimations() {
        // Animation d'apparition progressive des graphiques
        document.querySelectorAll('canvas, .plotly-graph-div').forEach(chart => {
            chart.style.opacity = '0';
            chart.style.transform = 'scale(0.8)';
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.style.transition = 'all 0.8s ease';
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'scale(1)';
                        }, 300);
                    }
                });
            });
            
            observer.observe(chart);
        });
    }

    // Configuration spéciale pour Chart.js si présent
    configureChartJS() {
        if (typeof Chart !== 'undefined') {
            Chart.defaults.animation.duration = 2000;
            Chart.defaults.animation.easing = 'easeOutQuart';
            
            // Configuration globale pour les graphiques
            Chart.defaults.plugins.legend.labels.usePointStyle = true;
            Chart.defaults.plugins.legend.labels.padding = 20;
        }
    }

    // Configuration pour Plotly si présent
    configurePlotly() {
        if (typeof Plotly !== 'undefined') {
            // Configuration par défaut pour les animations Plotly
            window.plotlyConfig = {
                displayModeBar: false,
                responsive: true,
                animation: {
                    duration: 1000,
                    easing: 'cubic-in-out'
                }
            };
        }
    }

    // Utilitaire pour ajouter des particules flottantes
    createFloatingParticles(container, count = 20) {
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: absolute;
                width: ${Math.random() * 4 + 2}px;
                height: ${Math.random() * 4 + 2}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                animation: float ${Math.random() * 3 + 4}s ease-in-out infinite;
                animation-delay: ${Math.random() * 2}s;
                pointer-events: none;
            `;
            container.appendChild(particle);
        }
    }

    // Smooth scroll pour la navigation
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Lazy loading pour les images
    setupLazyLoading() {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// CSS dynamique pour les animations
const animationStyles = `
@keyframes ripple {
    0% { transform: scale(0); opacity: 1; }
    100% { transform: scale(4); opacity: 0; }
}

.chart-container.visible {
    opacity: 1 !important;
    transform: translateY(0) !important;
}

.lazy {
    opacity: 0;
    transition: opacity 0.3s;
}

.loaded {
    opacity: 1;
}
`;

// Injection des styles
const styleSheet = document.createElement('style');
styleSheet.textContent = animationStyles;
document.head.appendChild(styleSheet);

// Initialisation automatique
const solarAnimations = new SolarProposalAnimations();

// Export pour utilisation dans Streamlit
if (typeof window !== 'undefined') {
    window.SolarProposalAnimations = SolarProposalAnimations;
    window.solarAnimations = solarAnimations;
}