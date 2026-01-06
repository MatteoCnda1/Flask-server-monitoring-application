class Config:
    """création du class qui permet de configurer des parametres et la connexion à quel database au moins on a pas besoin de réécrire ces lignes plusieurs fois !"""
    SQLALCHEMY_DATABASE_URI = 'mariadb+mariadbconnector://qamu:qamu@127.0.0.1/appli_superv'
    SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_size': 10,
                }

