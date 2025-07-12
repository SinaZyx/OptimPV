"""
Tests simplifiés pour vérifier le fonctionnement de base du module de répartition
Sans dépendance à Streamlit
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Tests directs des modèles (sans dépendance Streamlit)
def test_models():
    """Test des modèles de données"""
    print("\n=== Test des modèles ===")
    
    try:
        from modules.repartition_keys.key_models import (
            RepartitionKey, RepartitionPeriod, RepartitionRule,
            KeyType, PeriodType, RuleType
        )
        
        # Test 1: Création d'une clé
        key = RepartitionKey(
            site_id="site_001",
            participant_name="Site A",
            value=25.5,
            key_type=KeyType.STATIC
        )
        assert key.value == 25.5
        print("✓ Création de clé réussie")
        
        # Test 2: Validation des valeurs
        try:
            invalid_key = RepartitionKey(
                site_id="site_001",
                participant_name="Site A",
                value=-5,  # Invalide
                key_type=KeyType.STATIC
            )
            print("✗ La validation aurait dû échouer")
        except ValueError:
            print("✓ Validation des valeurs négatives OK")
        
        # Test 3: Période avec clés
        keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 30.0, KeyType.STATIC)
        ]
        
        period = RepartitionPeriod(
            period_id="period_001",
            period_type=PeriodType.MONTHLY,
            period_name="Janvier 2024",
            keys=keys
        )
        
        assert period.total_validation == True
        print("✓ Validation de période réussie (somme = 100%)")
        
        # Test 4: Sérialisation
        key_dict = key.to_dict()
        key_restored = RepartitionKey.from_dict(key_dict)
        assert key_restored.value == key.value
        print("✓ Sérialisation/désérialisation OK")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans les tests de modèles: {e}")
        return False


def test_validators():
    """Test des validateurs"""
    print("\n=== Test des validateurs ===")
    
    try:
        from modules.repartition_keys.key_models import RepartitionKey, KeyType
        from modules.repartition_keys.key_validators import quick_validate_keys
        
        # Test 1: Clés valides
        valid_keys = [
            RepartitionKey("site_001", "Site A", 25.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 50.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
        ]
        
        is_valid, msg = quick_validate_keys(valid_keys)
        assert is_valid == True
        print("✓ Validation de clés valides OK")
        
        # Test 2: Clés invalides (somme != 100)
        invalid_keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC)
        ]
        
        is_valid, msg = quick_validate_keys(invalid_keys)
        assert is_valid == False
        assert "70" in msg  # La somme fait 70%
        print("✓ Détection de somme incorrecte OK")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans les tests de validateurs: {e}")
        return False


def test_calculations():
    """Test des calculs de base"""
    print("\n=== Test des calculs ===")
    
    try:
        import pandas as pd
        import numpy as np
        from modules.repartition_keys.key_models import RepartitionKey, KeyType
        from modules.repartition_keys.key_calculations import apply_static_keys
        
        # Créer des données de test
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        production = pd.Series(
            data=np.array([0, 0, 0, 0, 0, 10, 50, 100, 150, 200,
                          250, 300, 300, 250, 200, 150, 100, 50,
                          10, 0, 0, 0, 0, 0]),
            index=dates
        )
        
        # Clés de répartition
        keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 45.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
        ]
        
        # Appliquer les clés
        result = apply_static_keys(production, keys)
        
        # Vérifications
        assert isinstance(result, pd.DataFrame)
        assert 'Production_Site A' in result.columns
        
        # Vérifier les allocations
        total_prod = production.sum()
        assert abs(result['Production_Site A'].sum() - total_prod * 0.30) < 0.01
        assert abs(result['Production_Site B'].sum() - total_prod * 0.45) < 0.01
        assert abs(result['Production_Site C'].sum() - total_prod * 0.25) < 0.01
        
        print("✓ Calculs de répartition statique OK")
        print(f"  Production totale: {total_prod:.0f} kWh")
        print(f"  Site A: {result['Production_Site A'].sum():.0f} kWh (30%)")
        print(f"  Site B: {result['Production_Site B'].sum():.0f} kWh (45%)")
        print(f"  Site C: {result['Production_Site C'].sum():.0f} kWh (25%)")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans les tests de calculs: {e}")
        return False


def test_storage():
    """Test du stockage JSON"""
    print("\n=== Test du stockage ===")
    
    try:
        import json
        import tempfile
        from modules.repartition_keys.key_models import RepartitionKey, KeyType
        
        # Créer des clés
        keys = [
            RepartitionKey("site_001", "Site A", 40.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 60.0, KeyType.STATIC)
        ]
        
        # Convertir en dictionnaire
        config = {
            "mode": "static",
            "keys": [k.to_dict() for k in keys],
            "created_at": "2024-01-01T00:00:00"
        }
        
        # Sauvegarder dans un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            temp_file = f.name
        
        # Recharger
        with open(temp_file, 'r') as f:
            loaded_config = json.load(f)
        
        # Vérifier
        assert loaded_config['mode'] == 'static'
        assert len(loaded_config['keys']) == 2
        assert loaded_config['keys'][0]['value'] == 40.0
        
        # Nettoyer
        os.unlink(temp_file)
        
        print("✓ Stockage et chargement JSON OK")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans les tests de stockage: {e}")
        return False


def main():
    """Exécuter tous les tests simplifiés"""
    print("="*60)
    print("TESTS SIMPLIFIÉS DU MODULE DE RÉPARTITION")
    print("(Sans dépendance Streamlit)")
    print("="*60)
    
    results = {
        "Modèles": test_models(),
        "Validateurs": test_validators(),
        "Calculs": test_calculations(),
        "Stockage": test_storage()
    }
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)
    
    total = len(results)
    success = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{test_name:.<40} {status}")
    
    print("-"*60)
    print(f"Total: {success}/{total} tests réussis")
    
    if success == total:
        print("\n✅ TOUS LES TESTS SONT PASSÉS !")
        print("Le module de répartition fonctionne correctement.")
    else:
        print("\n❌ Certains tests ont échoué.")
    
    return success == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)