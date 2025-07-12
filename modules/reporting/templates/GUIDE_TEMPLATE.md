# 📄 Guide d'Utilisation de Votre Template Word

## 🎯 **Comment Utiliser Votre Template Professionnelle**

### **1. 📁 Emplacement de la Template**

Votre template doit être placée dans :
```
/modules/reporting/templates/Business-Proposal-Template.docx
```

✅ **C'est déjà fait !** J'ai détecté votre template à cet emplacement.

### **2. 📝 Placeholders Disponibles**

Dans votre template Word, vous pouvez utiliser ces placeholders qui seront automatiquement remplacés par les vraies données OptimPV :

#### **Informations Client/Projet**
- `[CLIENT_NAME]` ou `{{CLIENT_NAME}}` : Nom du client
- `[PROJECT_NAME]` ou `{{PROJECT_NAME}}` : Nom du projet
- `[DATE]` ou `{{DATE}}` : Date du jour (format DD/MM/YYYY)
- `[YEAR]` ou `{{YEAR}}` : Année courante

#### **Données Techniques**
- `[PUISSANCE]` ou `{{PUISSANCE}}` : Puissance installée (ex: "25 kWc")
- `[PUISSANCE_KWC]` ou `{{PUISSANCE_KWC}}` : Puissance en nombre seul (ex: "25")
- `[AUTONOMIE]` ou `{{AUTONOMIE}}` : Taux d'autonomie (ex: "40%")
- `[PRIX_SOLAIRE]` ou `{{PRIX_SOLAIRE}}` : Prix du kWh solaire (ex: "0.160€/kWh")
- `[PRIX_KWH]` ou `{{PRIX_KWH}}` : Idem avec unité

#### **Données Financières**
- `[ECONOMIE_ANNUELLE]` ou `{{ECONOMIE_ANNUELLE}}` : Économie annuelle (ex: "2 500€")
- `[ECONOMIE_AN]` ou `{{ECONOMIE_AN}}` : Économie sans le symbole €
- `[ECONOMIE_20ANS]` ou `{{ECONOMIE_20ANS}}` : Économie sur 20 ans (ex: "50 000€")
- `[ECONOMIE_TOTALE]` ou `{{ECONOMIE_TOTALE}}` : Idem sans symbole €
- `[ROI]` ou `{{ROI}}` : Retour sur investissement (ex: "50K€")

#### **Informations Entreprise**
- `[COMPANY]` : "OptimPV"
- `[CONTACT_EMAIL]` : Email de contact
- `[CONTACT_PHONE]` : Téléphone de contact
- `[WEBSITE]` : Site web

#### **Graphiques (Optionnel)**
Si vous voulez insérer des graphiques, placez ces placeholders sur une ligne vide :
- `[CHART_DASHBOARD]` : Graphique dashboard principal
- `[CHART_ROI]` : Graphique évolution ROI
- `[CHART_COMPETITIVE]` : Graphique avantage concurrentiel

### **3. 🎨 Comment Modifier Votre Template**

1. **Ouvrez** `Business-Proposal-Template.docx` dans Word
2. **Insérez** les placeholders où vous voulez les données dynamiques
3. **Conservez** votre mise en forme (polices, couleurs, logos, etc.)
4. **Sauvegardez** la template

#### **Exemple Concret**

Dans votre template Word, écrivez :
```
Cher [CLIENT_NAME],

Nous sommes ravis de vous présenter notre proposition pour [PROJECT_NAME].

Avec une installation de [PUISSANCE], vous bénéficierez de :
- Une autonomie énergétique de [AUTONOMIE]
- Des économies annuelles de [ECONOMIE_ANNUELLE]
- Un prix solaire fixe de [PRIX_SOLAIRE]

Sur 20 ans, cela représente [ECONOMIE_20ANS] d'économies !
```

Sera transformé en :
```
Cher Entreprise ABC,

Nous sommes ravis de vous présenter notre proposition pour Projet Solaire ABC.

Avec une installation de 25 kWc, vous bénéficierez de :
- Une autonomie énergétique de 40%
- Des économies annuelles de 2 500€
- Un prix solaire fixe de 0.160€/kWh

Sur 20 ans, cela représente 50 000€ d'économies !
```

### **4. 🚀 Utilisation dans OptimPV**

1. **Allez** dans l'onglet "Rapports"
2. **Remplissez** le nom du client et du projet
3. **Cliquez** sur "📄 GÉNÉRER AVEC VOTRE TEMPLATE WORD"
4. **Téléchargez** le document généré

### **5. 💡 Conseils Pro**

#### **✅ FAIRE**
- Utilisez des styles Word pour une mise en forme cohérente
- Placez votre logo et vos éléments graphiques fixes dans la template
- Utilisez des tableaux Word pour structurer les données
- Créez des en-têtes et pieds de page avec vos coordonnées

#### **❌ ÉVITER**
- Ne pas mettre de placeholders dans les images
- Éviter les placeholders dans les formes et SmartArt
- Ne pas couper un placeholder sur plusieurs lignes

### **6. 🔍 Analyser Votre Template**

Pour voir quels placeholders sont détectés dans votre template :

```python
cd modules/reporting/docx_system
python template_based_generator.py
```

Cela listera tous les placeholders trouvés.

### **7. 🎯 Templates Multiples**

Vous pouvez avoir plusieurs templates :
- `Business-Proposal-Template.docx` : Proposition commerciale
- `Technical-Report-Template.docx` : Rapport technique
- `Executive-Summary-Template.docx` : Résumé exécutif

Il suffit de modifier le nom dans `template_based_generator.py`.

### **8. 🆘 Dépannage**

**Problème** : Les placeholders ne sont pas remplacés
- **Solution** : Vérifiez l'orthographe exacte des placeholders
- **Astuce** : Utilisez Ctrl+H dans Word pour voir tous les placeholders

**Problème** : La mise en forme est perdue
- **Solution** : Les placeholders doivent être dans un seul "run" Word
- **Astuce** : Retapez le placeholder d'un coup sans formatage

**Problème** : Les graphiques ne s'insèrent pas
- **Solution** : Le placeholder doit être seul sur sa ligne
- **Astuce** : Centrez le paragraphe contenant le placeholder

---

## 🎉 **Avantages de Votre Approche**

✅ **Design 100% personnalisé** : Votre charte graphique exacte
✅ **Contrôle total** : Vous maîtrisez chaque élément
✅ **Facilité** : Modifiez dans Word, pas dans le code
✅ **Professionnel** : Exactement comme votre designer l'a conçu
✅ **Évolutif** : Changez la template sans toucher au code

---

**📞 Besoin d'aide ?** Les placeholders dans ce guide sont tous supportés et testés !