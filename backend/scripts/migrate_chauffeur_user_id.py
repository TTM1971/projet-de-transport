"""
Ajoute la colonne chauffeurs.user_id si elle n'existe pas (PostgreSQL).
À exécuter une fois : python scripts/migrate_chauffeur_user_id.py
"""
from sqlalchemy import text

from database import engine


def main():
    stmts = [
        """
        ALTER TABLE chauffeurs
        ADD COLUMN IF NOT EXISTS user_id INTEGER UNIQUE
        """,
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'chauffeurs_user_id_fkey'
            ) THEN
                ALTER TABLE chauffeurs
                ADD CONSTRAINT chauffeurs_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
    ]
    with engine.connect() as conn:
        for s in stmts:
            try:
                conn.execute(text(s))
                conn.commit()
            except Exception as e:
                print("Note:", e)


if __name__ == "__main__":
    main()
    print("Migration chauffeurs.user_id terminée.")
