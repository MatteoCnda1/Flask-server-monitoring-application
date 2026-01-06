#!/usr/bin/env python3
from fabric import Connection
import datetime 
from abc import ABC, abstractmethod
import os


class Evenement(ABC):
    """Classe abstraite représentant un événement système"""
    
    def __init__(self, ident: int, dh: datetime.datetime, hote: str, msg: str):
        if ident <= 0:
            raise ValueError("id must be positive")
        if not isinstance(ident, int):
            raise TypeError("id must be an integer")
            
        self._ident = ident
        self._date_heure = dh
        self._hote = hote
        self._msg = msg
        
    @property
    def identification(self):
        return self._ident
        
    @abstractmethod
    def info(self):
        """Retourne un dictionnaire avec les informations de l'événement"""
        infoo = {
            "id": self._ident,
            "date_heure": self._date_heure,
            "hote": self._hote,
            "msg": self._msg
        }
        return infoo
            
    @classmethod
    def extrait(cls, num: int, ligne: str):
        """
        Méthode permettant de renvoyer un objet evenement selon son entrée service ou kernel
        Supporte les formats BSD et RFC3339
        """
        if num <= 0:
            raise ValueError("num must be positive")
        if not isinstance(num, int):
            raise TypeError("num must be an integer")
        if not isinstance(ligne, str):
            raise TypeError("ligne must be a str")
            
        ligne = ligne.strip()
        if not ligne:
            raise ValueError("La ligne est vide")
        
        # Détection du format de log
        if ligne[0].isdigit() and 'T' in ligne[:20]:
            # Format RFC3339/ISO 8601 : 2025-12-15T16:25:21.568760+01:00 srv-001 systemd[809]: ...
            return cls._extrait_rfc3339(num, ligne)
        else:
            # Format BSD : Dec 15 16:25:21 srv-001 systemd[809]: ...
            return cls._extrait_bsd(num, ligne)
    
    @classmethod
    def _extrait_bsd(cls, num: int, ligne: str):
        """Parse le format BSD traditionnel : Dec 15 16:25:21 host service[pid]: message"""
        parts = ligne.split(maxsplit=4)
        
        if len(parts) < 5:
            raise ValueError("Ligne BSD mal formée")
        
        month = parts[0]
        day = parts[1]
        time_str = parts[2]
        host = parts[3]
        rest = parts[4]
        
        # Construire le datetime
        now = datetime.datetime.today()
        date_str = f"{month} {day} {now.year} {time_str}"
        dh = datetime.datetime.strptime(date_str, "%b %d %Y %H:%M:%S")
        
        # Si la date est dans le futur, c'est l'année précédente
        if dh > now:
            dh = dh.replace(year=dh.year - 1)
        
        return cls._parse_message(num, dh, host, rest)
    
    @classmethod
    def _extrait_rfc3339(cls, num: int, ligne: str):
        """Parse le format RFC3339 : 2025-12-15T16:25:21.568760+01:00 host service[pid]: message"""
        parts = ligne.split(maxsplit=2)
        
        if len(parts) < 3:
            raise ValueError("Ligne RFC3339 mal formée")
        
        timestamp_str = parts[0]  # 2025-12-15T16:25:21.568760+01:00
        host = parts[1]           # srv-001
        rest = parts[2]           # systemd[809]: ...
        
        # Parser le timestamp RFC3339
        # Format : 2025-12-15T16:25:21.568760+01:00
        # On extrait : YYYY-MM-DD et HH:MM:SS
        try:
            date_part = timestamp_str.split('T')[0]  # 2025-12-15
            time_part = timestamp_str.split('T')[1].split('.')[0]  # 16:25:21
            
            dh = datetime.datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            raise ValueError(f"Erreur parsing timestamp RFC3339: {e}")
        
        return cls._parse_message(num, dh, host, rest)
    
    @classmethod
    def _parse_message(cls, num: int, dh: datetime.datetime, host: str, rest: str):
        """Parse la partie message (commune aux deux formats)"""
        # Vérifier si c'est une entrée kernel ou service
        if rest.startswith("kernel"):
            # Entrée kernel : kernel: [12345.678] message
            entry_type = "kernel"
            rest = rest[len("kernel: "):]
            
            # Le timestamp est entre crochets []
            timestamp_end = rest.find("]")
            if timestamp_end == -1:
                raise ValueError("Format kernel invalide : pas de ] trouvé")
            
            timestamp = rest[1:timestamp_end]
            timestamp = float(timestamp)
            message = rest[timestamp_end+2:].strip()
            
            return EvenementNoyau(num, dh, host, timestamp, message)
        else:
            # Entrée service : service[pid]: message
            parts_service = rest.split(":", 1)
            
            if len(parts_service) < 2:
                raise ValueError("Format service invalide : pas de : trouvé")
            
            service_full = parts_service[0]  # ex: "systemd[809]"
            message = parts_service[1].strip()
            
            # Extraire le nom du service et le PID
            idx1 = service_full.find("[")
            idx2 = service_full.find("]")
            
            if idx1 == -1 or idx2 == -1:
                raise ValueError("Format service[pid] invalide")
            
            service_name = service_full[:idx1]
            pid = int(service_full[idx1+1:idx2])
            
            return EvenementService(num, dh, host, service_name, pid, message)
    
    def __eq__(self, o):
        if not isinstance(o, Evenement):
            return NotImplemented
        return self.identification == o.identification
        
    def __gt__(self, o):
        if not isinstance(o, Evenement):
            return NotImplemented
        return self.identification > o.identification
        
    def __lt__(self, o):
        if not isinstance(o, Evenement):
            return NotImplemented
        return self.identification < o.identification
        
    def __hash__(self):
        return hash(self.identification)


class EvenementService(Evenement):
    """Événement provenant d'un service système"""
    
    def __init__(self, ident: int, dh: datetime.datetime, hote: str, serv: str, pid: int, msg: str):
        if pid <= 0:
            raise ValueError("pid doit être positif")
        if not isinstance(pid, int):
            raise TypeError("pid doit être un integer")
        if not isinstance(serv, str):
            raise TypeError("serv doit être un str")
        if not isinstance(dh, datetime.datetime):
            raise TypeError("dh doit être un objet datetime.datetime")
        if not isinstance(hote, str):
            raise TypeError("hote doit être un str")
        if not isinstance(ident, int):
            raise TypeError("ident doit être un integer")
        if ident <= 0:
            raise ValueError("ident doit être sup à 0")
        if not isinstance(msg, str):
            raise TypeError("msg doit être un str")
        
        super().__init__(ident, dh, hote, msg)
        
        self._pid = pid
        self._service = serv
        
    def __repr__(self):
        return (f"EvenementService(service={self._service}, pid={self._pid}, "
                f"id={self._ident}, host={self._hote}, date={self._date_heure}, "
                f"message={self._msg[:50]}...)")
        
    def info(self):
        """Retourne un dictionnaire avec toutes les informations"""
        base = super().info()
        base.update({
            "service": self._service,
            "pid": self._pid
        })
        return base


class EvenementNoyau(Evenement):
    """Événement provenant du noyau (kernel)"""
    
    def __init__(self, ident: int, dh: datetime.datetime, hote: str, tmstp: float, msg: str):
        if ident <= 0:
            raise ValueError("ident doit être positif")
        if not isinstance(ident, int):
            raise TypeError("ident doit être un int")
        if not isinstance(dh, datetime.datetime):
            raise TypeError("dh doit être un objet datetime.datetime")
        if not isinstance(hote, str):
            raise TypeError("hote doit être un str")
        if not isinstance(tmstp, float):
            raise TypeError("tmstp doit être un float")
        if tmstp < 0:  # Peut être 0
            raise ValueError("tmstp doit être positif ou nul")
        if not isinstance(msg, str):
            raise TypeError("msg doit être un str")
        
        super().__init__(ident, dh, hote, msg)
        
        self._timestamp = tmstp
        self._service = "kernel"
        
    def info(self):
        """Retourne un dictionnaire avec toutes les informations"""
        base = super().info()
        base.update({
            "service": self._service,
            "timestamp": self._timestamp
        })
        return base
     
    def __repr__(self):
        return (f"EvenementNoyau(service={self._service}, timestamp={self._timestamp}, "
                f"id={self._ident}, host={self._hote}, date={self._date_heure}, "
                f"message={self._msg[:50]}...)")


class Journal:
    """Représente un journal de logs système"""
    
    def __init__(self, nom_fichier: str = None, lignes: list = None):
        """
        Peut être initialisé soit avec un fichier, soit avec des lignes directement
        
        Args:
            nom_fichier: Chemin vers un fichier de logs
            lignes: Liste de lignes de logs
        """
        self._fichier = nom_fichier
        self._evenements = []
        
        if lignes:
            self._charger_depuis_lignes(lignes)
        elif nom_fichier:
            self.rafraichit()
    
    def liste(self):
        """Renvoie la liste des objets Événement de ce journal"""
        return self._evenements
    
    def _charger_depuis_lignes(self, lignes):
        """Charge les événements depuis une liste de lignes"""
        self._evenements = []
        num = 1
        
        for ligne in lignes:
            ligne = ligne.strip()
            if not ligne:
                continue
            
            try:
                evt = Evenement.extrait(num, ligne)
                self._evenements.append(evt)
                num += 1
            except (ValueError, TypeError, IndexError) as e:
                # Ignorer les lignes mal formées
                
                pass
    
    def rafraichit(self):
        """Recharge les événements depuis le fichier"""
        if not self._fichier:
            return []
        
        self._evenements = []
        
        try:
            with open(self._fichier, 'r', encoding='utf8') as f:
                lignes = f.readlines()
            
            num = 1
            for ligne in lignes:
                ligne = ligne.strip()
                if not ligne:
                    continue
                
                try:
                    evt = Evenement.extrait(num, ligne)
                    self._evenements.append(evt)
                    num += 1
                except (ValueError, TypeError, IndexError):
                    pass
        except FileNotFoundError:
            self._evenements = []
        
        return self.liste()
    
    @staticmethod
    def recuperer_logs_distant(ip: str, user: str = 'superv', key_file: str = None, 
                               log_path: str = '/var/log/syslog', nb_lignes: int = 100):
        """
        Récupère les logs d'un serveur distant via ssh
        """
        # Définir le chemin par défaut de la clé
        if key_file is None:
            key_file = os.path.expanduser('~/.ssh/id_rsa_superv')
        
        try:
            print(f"[DEBUG] Tentative de connexion à {ip} avec user={user} et key={key_file}")
            
            # Vérifier que la clé existe
            if not os.path.exists(key_file):
                print(f"[ERREUR] Clé SSH non trouvée : {key_file}")
                return None
            
            # Connexion SSH
            cnx = Connection(
                host=ip,
                user=user,
                connect_kwargs={"key_filename": key_file}
            )
            
            print(f"[DEBUG] Connexion établie, récupération de {nb_lignes} lignes de {log_path}")
            
            # Récupérer les dernières lignes du log
            command = f'tail -n {nb_lignes} {log_path}'
            result = cnx.run(command, hide=True)
            
            print(f"[DEBUG] Commande exécutée, {len(result.stdout)} caractères reçus")
            
            # Fermer la connexion
            cnx.close()
            
            # Créer un Journal avec les lignes récupérées
            lignes = result.stdout.split('\n')
            print(f"[DEBUG] {len(lignes)} lignes à traiter")
            
            journal = Journal(lignes=lignes)
            
            print(f"[DEBUG] Journal créé avec {len(journal.liste())} événements")
            
            return journal
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la récupération des logs depuis {ip}: {e}")
            import traceback
            traceback.print_exc()
            return None


