#!/bin/env python3
import app
from config import Config

appli = app.create_app(Config)

if __name__ == '__main__':
    appli.run(debug=True)

    """Ici on est au point d'entrée principal de l'application on peut la lancer dans le teminal en faisant ./run.py"""

