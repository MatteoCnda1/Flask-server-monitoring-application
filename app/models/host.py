from app import db
from flask import Flask
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import String, Numeric, Integer
from decimal import Decimal
from ipaddress import IPv4Address , ip_address
from werkzeug.security import generate_password_hash, check_password_hash

class Host(db.Model):
    __tablename__ = "machines"
    """Ici grace à cette classe on 'map' la table sur laquelle on travaille selon les specs donnée"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True , nullable=False)
    ipv4: Mapped[str] = mapped_column(String(15), nullable=False)

    @staticmethod
    def ajoute_host(name, ip):

        try:
            ipv4 = IPv4Address(ip)
            """transformation de la chaine de caractere ip en object IPv4address pour verifier      sa validité"""
        except ValueError as v:
            return 'Type a valid ip address'
        """sinon valuerror et envoie d'un message à l'utilisateur"""
        
        if len(name) > 255:
             return "name too large. You should give a name under 253 characters"

        existing_machine = db.session.query(Host).filter(Host.hostname == name).first()
        if existing_machine:
            return "Server already existing."

        existing_ip = db.session.query(Host).filter(Host.ipv4 == ip).first()
        if existing_ip:
            return "IP already in use."


        host = Host(
                hostname = name,
                ipv4=ip)

        db.session.add(host)

        try:
            db.session.commit()

        except IntegrityError as i:
            db.session.rollback()
            return "existing name"
    
        except Exception as e:
            db.session.rollback()
            print('erreur :',e)
        finally:
            db.session.close()


    @staticmethod
    def supprime_host(nom):
        host = Host.query.get(nom)
        if host:
            db.session.delete(host)
            db.session.commit()
        db.session.close()

    @staticmethod
    def get_host_by_id(host_id):
        return Host.query.get(host_id)

    @staticmethod
    def modify_server(host_id, hostname=None, ipv4=None):

            host = Host.query.get(host_id)
                
            if not host:
                return "Server not found"
                
            if hostname and hostname != host.hostname:
                existing = Host.query.filter(Host.hostname == hostname).first()
                if existing:
                    return "This hostname already exist !"
                host.hostname = hostname
            
            if ipv4:
                host.ipv4 = ipv4

            try:
                db.session.commit()
                return "success"
            except Exception as e:
                db.session.rollback()
                return f"Erreur : {e}"
            


class User(db.Model):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_user: Mapped[str] = mapped_column(String(100), unique=True)
    mdp: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False)

    @staticmethod
    def add_user(username, pwd, role):
        if not isinstance(username, str):
            raise TypeError("Bad type")
        if not isinstance(pwd, str):
            raise TypeError("Bad type")
        if not isinstance(role, int):
            raise TypeError("Bad type")


        if len(username) > 255:
            return f"Username too long !"

        if role != 1 or 2 or 3:
            return ValueError("Bad value for the role")
        
        existing_user = db.session.query(User).filter(User.nom_user ==username).first()
        if existing_user:
            return "User already existing"

        user = User(
                nom_user = username,
                mdp = generate_password_hash(pwd, method='pbkdf2:sha256'),
                role_id = role)

        db.session.add(user)

        try:
            db.session.commit()

        except IntegrityError as i:
            db.session.rollback()
            return "user already existing"
        
        except Exception as e:
            db.session.rollback()
            print("erreur : ",e)
        finally:
            db.session.close()

    @staticmethod
    def del_user(nom):
        user = User.query.get(nom)
        if user:
            db.session.delete(user)
            db.session.commit()
        db.session.close()

    @staticmethod
    def authentificate(username, password):
        user = db.session.query(User).filter_by(nom_user=username).first()

        if user and check_password_hash(user.mdp, password):
            return user
        return None

    @staticmethod
    def create_user(username, password, role):
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(nom_user=username, mdp = hashed_password, role_id = role)
        db.session.add(new_user)

        try:
            db.session.commit()
        except IntegrityError as i:
            db.session.rollback()
            return "user already existing"

        except Exception as e:
            db.session.rollback()
            print("Erreur :", e )
        finally:
            db.session.close()

    @staticmethod
    def modify_user(user_id, username=None, password=None, role=None):

            user = User.query.get(user_id)
            
            if not user:
                return "Utilisateur non trouvé"
            
            if username and username != user.nom_user:
                existing = User.query.filter(User.nom_user == username).first()
                if existing:
                    return "Ce nom d'utilisateur existe déjà"
                user.nom_user = username
            
            if password:
                user.mdp = generate_password_hash(password, method='pbkdf2:sha256')
            
            if role is not None:
                if role not in [1, 2, 3]:
                    return "Rôle invalide"
                user.role_id = role
            

            try:
                db.session.commit()
                return "success"
            except Exception as e:
                db.session.rollback()
                return f"Erreur : {e}"
            


