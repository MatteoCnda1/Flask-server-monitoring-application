#!/usr/bin/python3

import sys
import logging
import os

# Configuration du logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Ajouter le path de l'environnement virtuel
sys.path.insert(0, '/home/qamu/r309/lib/python3.11/site-packages')

# Ajouter le path de l'application
sys.path.insert(0, '/home/qamu/appli_supervision')

# Changer le répertoire de travail
os.chdir('/home/qamu/appli_supervision')

# Importer l'application 
try:
    import app
    from config import Config
    
    application = app.create_app(Config)
    
    logging.info("Application Flask créée avec succès")
except Exception as e:
    logging.error(f"Erreur lors de l'import : {e}")
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise
