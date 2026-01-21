"""
Script de migration pour ajouter les nouvelles colonnes à la table users
"""
import sys
from database import SessionLocal
from sqlalchemy import text

def migrate_users_table():
    """Ajouter les colonnes manquantes à la table users"""
    db = SessionLocal()
    try:
        # Liste des colonnes à ajouter avec leurs types et valeurs par défaut
        migrations = [
            ("first_name", "VARCHAR", "NULL"),
            ("last_name", "VARCHAR", "NULL"),
            ("email", "VARCHAR", "NULL"),
            ("phone", "VARCHAR", "NULL"),
            ("avatar_url", "VARCHAR", "NULL"),
            ("organization_id", "INTEGER", "NULL"),
            ("hire_date", "TIMESTAMP", "NULL"),
            ("is_active", "BOOLEAN", "TRUE"),
            ("last_login", "TIMESTAMP", "NULL"),
            ("created_at", "TIMESTAMP", "CURRENT_TIMESTAMP"),
            ("preferences", "JSONB", "NULL")
        ]
        
        print("=== Migration de la table users ===")
        
        for column_name, column_type, default_value in migrations:
            try:
                # Vérifier si la colonne existe déjà
                check_query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='{column_name}'
                """)
                result = db.execute(check_query).fetchone()
                
                if result:
                    print(f"→ Colonne '{column_name}' existe déjà, ignorée")
                else:
                    # Ajouter la colonne
                    if default_value == "NULL":
                        alter_query = text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    else:
                        alter_query = text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
                    
                    db.execute(alter_query)
                    db.commit()
                    print(f"✓ Colonne '{column_name}' ajoutée")
            except Exception as e:
                print(f"✗ Erreur pour '{column_name}': {e}")
                db.rollback()
        
        # Créer les index si nécessaire
        try:
            # Index pour email (unique)
            db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email) WHERE email IS NOT NULL"))
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users(organization_id)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_is_active ON users(is_active)"))
            db.commit()
            print("✓ Index créés")
        except Exception as e:
            print(f"Note: Erreur lors de la création des index (peut déjà exister): {e}")
            db.rollback()
        
        # Mettre à jour les utilisateurs existants avec des emails par défaut
        try:
            update_query = text("""
                UPDATE users 
                SET email = username || '@transport.local',
                    is_active = TRUE,
                    created_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                WHERE email IS NULL
            """)
            db.execute(update_query)
            db.commit()
            print("✓ Utilisateurs existants mis à jour avec des emails par défaut")
        except Exception as e:
            print(f"Note: {e}")
            db.rollback()
        
        print("\n=== Migration terminée ===")
        return True
        
    except Exception as e:
        print(f"Erreur lors de la migration: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = migrate_users_table()
    sys.exit(0 if success else 1)
