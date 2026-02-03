# Phase 1 - Issues à corriger

## Issues Ruff (Linting)

### Priorité Haute
- [ ] `core/engine/builder.py:29` - Utiliser `raise ... from err` pour les exceptions
- [ ] `core/engine/builder.py:215,227` - Remplacer `except:` bare par des exceptions spécifiques
- [ ] `core/scripts/create_exporter.py:65` - Variable `has_amd64` non utilisée

### Priorité Moyenne
- [ ] `core/engine/builder.py:86` - Combiner les `with` statements
- [ ] `core/engine/site_generator.py:81` - Simplifier la création de `categories`

## Issues Bandit (Sécurité)

### Priorité Haute - À corriger IMMÉDIATEMENT
- [ ] **B113** `core/engine/builder.py:73,156` - Ajouter `timeout` aux appels `requests.get()`
- [ ] **B113** `core/engine/watcher.py:32` - Ajouter `timeout` à `requests.get()`
- [ ] **B701** `core/engine/builder.py:179` - Activer `autoescape=True` dans Jinja2

### Priorité Basse (acceptable pour scripts internes)
- [ ] B605/B607 `core/render_test.py:949` - `os.system()` usage
- [ ] B603 `core/scripts/create_exporter.py:28` - subprocess usage (acceptable)

## Issues MyPy (Type Checking)

### À traiter progressivement
- Plusieurs erreurs de typage dans les modules
- Stratégie : Ajouter les types progressivement fichier par fichier
- Commencer par les nouveaux fichiers (tests, logging)

## Corrections prioritaires pour commit

1. Ajouter timeout aux requests
2. Activer autoescape Jinja2
3. Fixer les bare except
4. Nettoyer variables inutilisées
