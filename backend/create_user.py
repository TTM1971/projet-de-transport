"""
Script pour créer un utilisateur de test dans la base de données
Usage: python create_user.py
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.user import User
from models.chauffeur import Chauffeur as ChauffeurModel
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
            "ville": "Ottawa",
            "description": "👨‍💼 Administrateur - Accès complet au système"
        },
        {
            "username": "agent_ottawa",
            "password": "agent123",
            "role": "agent",
            "ville": "Ottawa",
            "description": "💰 Agent Ottawa - Vente de billets"
        },
        {
            "username": "gestionnaire_ottawa",
            "password": "gest123",
            "role": "gestionnaire",
            "ville": "Ottawa",
            "description": "🚌 Gestionnaire Ottawa - Gestion locale"
        },
        {
            "username": "gestionnaire_montreal",
            "password": "gest123",
            "role": "gestionnaire",
            "ville": "Montréal",
            "description": "🚌 Gestionnaire Montréal - Gestion locale"
        },
        {
            "username": "maintenance",
            "password": "maint123",
            "role": "maintenance",
            "ville": "Ottawa",
            "description": "🔧 Équipe Maintenance - Gestion atelier et maintenance"
        },
        {
            "username": "chauffeur_demo",
            "password": "chauffeur123",
            "role": "chauffeur",
            "ville": "Ottawa",
            "description": "🚗 Chauffeur - Planning personnel et trajets",
        },
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
                # Réactiver les comptes de démo s'ils ont été désactivés (ex. flux d'approbation)
                if not existing.is_active:
                    existing.is_active = True
                    db.commit()
                    db.refresh(existing)
                    print(
                        f"✅ Compte '{user_data['username']}' réactivé (était inactif — connexion impossible avant)."
                    )
                else:
                    print(
                        f"⚠️  L'utilisateur '{user_data['username']}' existe déjà (ID: {existing.id}, Rôle: {existing.role})"
                    )
                created_users.append(existing)
                continue
            
            # Créer l'utilisateur (comptes de démo : actifs tout de suite)
            new_user = User(
                username=user_data["username"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                ville=user_data.get("ville"),
                is_active=True,
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
        print("\n5. 🚗 CHAUFFEUR (démo)")
        print("   Username: chauffeur_demo")
        print("   Password: chauffeur123")
        print("   Accès: Espace chauffeur (horaires, trajets)")
        print("\n" + "="*70)

        # Lier le compte chauffeur_demo à la première fiche chauffeur (si colonne user_id)
        u_ch = db.query(User).filter(User.username == "chauffeur_demo").first()
        ch = db.query(ChauffeurModel).order_by(ChauffeurModel.id).first()
        if u_ch and ch and getattr(ch, "user_id", None) is None:
            try:
                ch.user_id = u_ch.id
                db.commit()
                print(f"\n✅ Compte chauffeur_demo lié au chauffeur ID {ch.id} ({ch.prenom} {ch.nom}).")
            except Exception as ex:
                db.rollback()
                print(
                    "\n⚠️  Impossible de lier chauffeur_demo (exécutez scripts/migrate_chauffeur_user_id.py puis relancez):",
                    ex,
                )

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
