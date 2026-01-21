"""
Script pour créer un utilisateur de test dans la base de données
Usage: python create_user.py
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.user import User
from auth.hash_password import hash_password

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

def create_default_users():
    """Crée tous les utilisateurs de test par rôle"""
    db: Session = SessionLocal()
    
    # Définition des utilisateurs à créer
    users_to_create = [
        {
            "username": "admin",
            "password": "admin123",
            "role": "admin",
            "description": "👨‍💼 Administrateur - Accès complet au système"
        },
        {
            "username": "agent",
            "password": "agent123",
            "role": "agent",
            "description": "💰 Agent de Vente - Vente de billets uniquement"
        },
        {
            "username": "gestionnaire",
            "password": "gest123",
            "role": "gestionnaire",
            "description": "🚌 Gestionnaire de Flotte - Gestion bus, lignes, destinations"
        },
        {
            "username": "maintenance",
            "password": "maint123",
            "role": "maintenance",
            "description": "🔧 Équipe Maintenance - Gestion atelier et maintenance"
        }
    ]
    
    created_users = []
    
    try:
        print("\n" + "="*70)
        print("🚀 CRÉATION DES UTILISATEURS DE TEST")
        print("="*70 + "\n")
        
        for user_data in users_to_create:
            # Vérifier si l'utilisateur existe déjà
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            
            if existing:
                print(f"⚠️  L'utilisateur '{user_data['username']}' existe déjà (ID: {existing.id}, Rôle: {existing.role})")
                created_users.append(existing)
                continue
            
            # Créer l'utilisateur
            new_user = User(
                username=user_data["username"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"]
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            created_users.append(new_user)
            
            print(f"✅ {user_data['description']}")
            print(f"   Username: {user_data['username']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Rôle: {user_data['role']}")
            print()
        
        print("="*70)
        print("📋 RÉSUMÉ DES IDENTIFIANTS")
        print("="*70)
        print("\n1. 👨‍💼 ADMINISTRATEUR")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Accès: TOUT (Dashboard, Gestion complète, Utilisateurs)")
        print("\n2. 💰 AGENT DE VENTE")
        print("   Username: agent")
        print("   Password: agent123")
        print("   Accès: Vente de billets uniquement")
        print("\n3. 🚌 GESTIONNAIRE DE FLOTTE")
        print("   Username: gestionnaire")
        print("   Password: gest123")
        print("   Accès: Bus, Lignes, Destinations, Suivi flotte")
        print("\n4. 🔧 ÉQUIPE MAINTENANCE")
        print("   Username: maintenance")
        print("   Password: maint123")
        print("   Accès: Maintenance, Suivi flotte (lecture)")
        print("\n" + "="*70)
        
        return created_users
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur lors de la création des utilisateurs: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_default_users()
    print("\n✨ Terminé ! Les utilisateurs sont prêts à être utilisés.")
