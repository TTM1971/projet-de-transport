"""
Script d'initialisation des données de base :
- Créer les rôles système
- Créer les permissions de base
- Assigner les permissions aux rôles
"""
from database import SessionLocal
from models.role import Role
from models.permission import Permission
from models.role_permission import role_permissions
from sqlalchemy.exc import IntegrityError

def init_roles():
    """Créer les rôles système"""
    db = SessionLocal()
    try:
        # Liste des rôles système
        system_roles = [
            {"name": "admin", "description": "Administrateur système - Accès complet", "is_system": True},
            {"name": "gestionnaire", "description": "Gestionnaire - Gestion opérationnelle", "is_system": True},
            {"name": "agent", "description": "Agent de vente - Vente de billets", "is_system": True},
            {"name": "maintenance", "description": "Personnel maintenance - Gestion atelier", "is_system": True},
        ]
        
        for role_data in system_roles:
            existing = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing:
                role = Role(**role_data)
                db.add(role)
                print(f"✓ Rôle créé : {role_data['name']}")
            else:
                print(f"→ Rôle existe déjà : {role_data['name']}")
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création des rôles : {e}")
        return False
    finally:
        db.close()

def init_permissions():
    """Créer les permissions de base"""
    db = SessionLocal()
    try:
        # Liste des ressources
        resources = ["user", "bus", "ligne", "destination", "billet", "depart", "chauffeur", 
                     "atelier", "ping", "organization", "role", "permission", "audit"]
        
        # Liste des actions
        actions = ["create", "read", "update", "delete", "export"]
        
        permissions_created = 0
        for resource in resources:
            for action in actions:
                existing = db.query(Permission).filter(
                    Permission.resource == resource,
                    Permission.action == action
                ).first()
                
                if not existing:
                    permission = Permission(
                        resource=resource,
                        action=action,
                        description=f"{action.capitalize()} {resource}"
                    )
                    db.add(permission)
                    permissions_created += 1
        
        db.commit()
        print(f"✓ {permissions_created} permissions créées")
        return True
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création des permissions : {e}")
        return False
    finally:
        db.close()

def assign_permissions_to_roles():
    """Assigner les permissions aux rôles système"""
    db = SessionLocal()
    try:
        # Récupérer les rôles
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        gestionnaire_role = db.query(Role).filter(Role.name == "gestionnaire").first()
        agent_role = db.query(Role).filter(Role.name == "agent").first()
        maintenance_role = db.query(Role).filter(Role.name == "maintenance").first()
        
        # Récupérer toutes les permissions
        all_permissions = db.query(Permission).all()
        
        # Admin : toutes les permissions
        if admin_role:
            admin_role.permissions = all_permissions
            print(f"✓ Permissions assignées au rôle admin ({len(all_permissions)} permissions)")
        
        # Gestionnaire : permissions sur les ressources opérationnelles (pas users, roles, audit)
        if gestionnaire_role:
            gestionnaire_perms = [p for p in all_permissions 
                                 if p.resource not in ["user", "role", "permission", "audit"]]
            gestionnaire_role.permissions = gestionnaire_perms
            print(f"✓ Permissions assignées au rôle gestionnaire ({len(gestionnaire_perms)} permissions)")
        
        # Agent : permissions limitées (read lignes, destinations, departs; create/read billets)
        if agent_role:
            agent_perms = [p for p in all_permissions 
                          if (p.resource in ["ligne", "destination", "depart"] and p.action == "read") or
                             (p.resource == "billet" and p.action in ["create", "read"])]
            agent_role.permissions = agent_perms
            print(f"✓ Permissions assignées au rôle agent ({len(agent_perms)} permissions)")
        
        # Maintenance : permissions sur bus, atelier, ping
        if maintenance_role:
            maintenance_perms = [p for p in all_permissions 
                               if p.resource in ["bus", "atelier", "ping"]]
            maintenance_role.permissions = maintenance_perms
            print(f"✓ Permissions assignées au rôle maintenance ({len(maintenance_perms)} permissions)")
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de l'assignation des permissions : {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== Initialisation de la base de données ===")
    print("\n1. Création des rôles système...")
    init_roles()
    
    print("\n2. Création des permissions...")
    init_permissions()
    
    print("\n3. Assignation des permissions aux rôles...")
    assign_permissions_to_roles()
    
    print("\n=== Initialisation terminée ===")
