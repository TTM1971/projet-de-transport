# Guide pour exécuter le script de génération de données

## Option 1 : Utiliser l'environnement virtuel existant

1. **Activer l'environnement virtuel** (dans PowerShell) :
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   ```

2. **Vérifier que les dépendances sont installées** :
   ```powershell
   pip install -r requirements.txt
   ```

3. **Exécuter le script** :
   ```powershell
   python run_seed.py
   ```

## Option 2 : Si l'activation du venv ne fonctionne pas

1. **Installer les dépendances directement** (si Python est installé globalement) :
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```

2. **Exécuter le script** :
   ```powershell
   python run_seed.py
   ```

## Option 3 : Utiliser Docker (si disponible)

Si vous utilisez Docker Compose, vous pouvez exécuter le script dans le conteneur :

```bash
docker-compose exec backend python run_seed.py
```

## Erreurs courantes

### "ModuleNotFoundError: No module named 'sqlalchemy'"

Cela signifie que les dépendances ne sont pas installées. Résolution :
```powershell
pip install -r requirements.txt
```

### "Cannot activate virtual environment"

Essayez d'utiliser directement le Python du venv :
```powershell
.\venv\Scripts\python.exe run_seed.py
```

Ou réinstallez les dépendances dans le venv :
```powershell
.\venv\Scripts\pip.exe install -r requirements.txt
.\venv\Scripts\python.exe run_seed.py
```
