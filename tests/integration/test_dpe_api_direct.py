#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test direct de l'API ADEME pour comprendre la syntaxe correcte
"""

import requests
import json

# Test avec différentes syntaxes de paramètres
print("TEST SYNTAXE API ADEME DPE")
print("=" * 60)

url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"

# Test 1: Avec Code_postal_(BAN) comme paramètre direct
print("\n1. Test avec Code_postal_(BAN) = 06130:")
print("-" * 40)

params = {
    'Code_postal_(BAN)': '06130',
    'size': 10
}

response = requests.get(url, params=params)
print(f"URL générée: {response.url}")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    total = data.get('total', 0)
    results = data.get('results', [])
    print(f"Total: {total}")
    
    if results:
        print(f"\nPremiers résultats:")
        for i, dpe in enumerate(results[:3]):
            print(f"  {i+1}. {dpe.get('Adresse_(BAN)', 'N/A')} - CP: {dpe.get('Code_postal_(BAN)', 'N/A')}")

# Test 2: Avec filter
print("\n\n2. Test avec filter[Code_postal_(BAN)]:")
print("-" * 40)

params = {
    'filter[Code_postal_(BAN)]': '06130',
    'size': 10
}

response = requests.get(url, params=params)
print(f"URL générée: {response.url}")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    total = data.get('total', 0)
    print(f"Total: {total}")

# Test 3: Avec where
print("\n\n3. Test avec where:")
print("-" * 40)

params = {
    'where': 'Code_postal_(BAN)="06130"',
    'size': 10
}

response = requests.get(url, params=params)
print(f"URL générée: {response.url}")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    total = data.get('total', 0)
    print(f"Total: {total}")

# Test 4: Avec q (query)
print("\n\n4. Test avec q (différentes syntaxes):")
print("-" * 40)

queries = [
    '06130',
    'Code_postal_(BAN):06130',
    'Code_postal_(BAN):"06130"',
    'Code_postal_(BAN) = "06130"'
]

for query in queries:
    params = {
        'q': query,
        'size': 10
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        print(f"  q='{query}' → Total: {total}")

# Test 5: Vérifier la doc de l'API
print("\n\n5. Documentation API:")
print("-" * 40)

api_info_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants"
response = requests.get(api_info_url)
if response.status_code == 200:
    info = response.json()
    print(f"Dataset ID: {info.get('id', 'N/A')}")
    print(f"Titre: {info.get('title', 'N/A')}")
    
    # Chercher des infos sur les paramètres de requête
    if 'rest' in info:
        print("\nParamètres REST disponibles:")
        for param in ['q', 'qs', 'q_mode', 'filter', 'where']:
            if param in info['rest']:
                print(f"  - {param}: supporté")