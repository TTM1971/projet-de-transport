from fastapi import APIRouter, Depends, HTTPException
from schemas.billet import Billet, BilletCreate, BilletUpdate
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.billet import Billet as BilletModel
from models.depart import Depart as DepartModel
from models.ligne import Ligne as LigneModel
from datetime import datetime
from middleware.dependencies import get_current_user, require_agent_or_admin, require_gestionnaire_or_admin
import uuid

router = APIRouter()


def _normalize_city(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s.lower() if s else None

@router.get("/", response_model=List[Billet])
def list_billets(
    skip: int = 0,
    limit: int = 100,
    ville: str | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Liste des billets - Admin et Gestionnaire voient tous les billets, Agents voient les leurs"""
    # Les agents voient seulement leurs billets
    if hasattr(current_user, 'role') and current_user.role == 'agent':
        billets = db.query(BilletModel).filter(BilletModel.agent_id == current_user.id).offset(skip).limit(limit).all()
    elif hasattr(current_user, 'role') and current_user.role == 'gestionnaire':
        city = _normalize_city(getattr(current_user, "ville", None))
        if not city:
            return []
        city_ligne_ids = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(f"{city},%")).subquery()
        billets = db.query(BilletModel).filter(BilletModel.ligne_id.in_(city_ligne_ids)).offset(skip).limit(limit).all()
    elif hasattr(current_user, 'role') and current_user.role == 'admin' and ville:
        city = _normalize_city(ville)
        city_ligne_ids = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(f"{city},%")).subquery()
        billets = db.query(BilletModel).filter(BilletModel.ligne_id.in_(city_ligne_ids)).offset(skip).limit(limit).all()
    else:
        billets = db.query(BilletModel).offset(skip).limit(limit).all()
    return billets

@router.get("/agent/{agent_id}", response_model=List[Billet])
def list_billets_by_agent(
    agent_id: int, 
    skip: int = 0, 
    limit: int = 1000,
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """Liste les billets vendus par un agent spécifique - Gestionnaire et Admin uniquement"""
    if hasattr(current_user, 'role') and current_user.role == 'agent' and current_user.id != agent_id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez voir que vos propres billets")
    # Limiter les résultats pour éviter les réponses trop lourdes
    if limit > 1000:
        limit = 1000
    billets = db.query(BilletModel).filter(BilletModel.agent_id == agent_id).offset(skip).limit(limit).all()
    return billets

@router.get("/{billet_id}", response_model=Billet)
def get_billet(billet_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Détails d'un billet - Agents peuvent voir seulement leurs billets"""
    billet = db.query(BilletModel).filter(BilletModel.id == billet_id).first()
    if not billet:
        raise HTTPException(status_code=404, detail="Billet non trouvé")
    
    # Les agents peuvent voir seulement leurs propres billets
    if hasattr(current_user, 'role') and current_user.role == 'agent' and billet.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'avez pas accès à ce billet")
    
    return billet

@router.post("/", response_model=Billet)
def create_billet(billet: BilletCreate, db: Session = Depends(get_db), current_user = Depends(require_agent_or_admin)):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Données reçues pour création de billet: {billet.model_dump()}")
        logger.info(f"Types: depart_id={type(billet.depart_id)}, bus_id={type(billet.bus_id)}, agent_id={type(billet.agent_id)}, montant={type(billet.montant)}")
    except Exception as e:
        logger.error(f"Erreur lors du logging: {e}")
    
    from models.bus import Bus as BusModel
    from models.destination import Destination as DestinationModel
    from models.ligne import Ligne as LigneModel
    from models.user import User as UserModel
    from models.chauffeur import Chauffeur as ChauffeurModel
    
    # Vérifier que le départ existe
    depart = db.query(DepartModel).filter(DepartModel.id == billet.depart_id).first()
    if not depart:
        raise HTTPException(status_code=404, detail="Départ non trouvé")
    
    # Vérifier que le départ a encore des places disponibles
    if depart.places_disponibles <= 0:
        raise HTTPException(status_code=400, detail="Plus de places disponibles pour ce départ")
    
    # Valider que le bus existe
    bus = db.query(BusModel).filter(BusModel.id == billet.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail=f"Bus avec ID {billet.bus_id} non trouvé")
    
    # Valider que la destination existe
    destination = db.query(DestinationModel).filter(DestinationModel.id == billet.destination_id).first()
    if not destination:
        raise HTTPException(status_code=404, detail=f"Destination avec ID {billet.destination_id} non trouvée")
    
    # Valider que l'agent existe
    agent = db.query(UserModel).filter(UserModel.id == billet.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent avec ID {billet.agent_id} non trouvé")
    if not agent.is_active:
        raise HTTPException(status_code=400, detail="L'agent n'est pas actif")
    
    # Les agents ne peuvent créer que leurs propres billets
    if hasattr(current_user, 'role') and current_user.role == 'agent':
        if billet.agent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Vous ne pouvez créer des billets que pour votre propre compte")
    
    # Valider la ligne si fournie
    if billet.ligne_id:
        ligne = db.query(LigneModel).filter(LigneModel.id == billet.ligne_id).first()
        if not ligne:
            raise HTTPException(status_code=404, detail=f"Ligne avec ID {billet.ligne_id} non trouvée")
    
    # Valider le chauffeur si fourni
    if billet.chauffeur_id:
        chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == billet.chauffeur_id).first()
        if not chauffeur:
            raise HTTPException(status_code=404, detail=f"Chauffeur avec ID {billet.chauffeur_id} non trouvé")
    
    # Utiliser les informations du départ si non fournies
    bus_id = billet.bus_id if billet.bus_id else depart.bus_id
    chauffeur_id = billet.chauffeur_id if billet.chauffeur_id else depart.chauffeur_id
    ligne_id = billet.ligne_id if billet.ligne_id else depart.ligne_id
    
    # Vérifier le mode de paiement
    valid_modes = ['espece', 'carte', 'mobile']
    if billet.mode_paiement not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Mode de paiement invalide. Modes acceptés: {', '.join(valid_modes)}")
    
    # Générer un code QR unique
    code_qr = str(uuid.uuid4())
    
    # Créer le billet
    db_billet = BilletModel(
        depart_id=billet.depart_id,
        bus_id=bus_id,
        destination_id=billet.destination_id,
        ligne_id=ligne_id,
        chauffeur_id=chauffeur_id,
        siege=billet.siege,
        agent_id=billet.agent_id,
        mode_paiement=billet.mode_paiement,
        montant=billet.montant,
        code_qr=code_qr,
        date_achat=datetime.utcnow(),
        nom_client=billet.nom_client,
        telephone_client=billet.telephone_client
    )
    db.add(db_billet)
    
    # Décrémenter le nombre de places disponibles
    depart.places_disponibles -= 1
    
    db.commit()
    db.refresh(db_billet)
    return db_billet

@router.put("/{billet_id}", response_model=Billet)
def update_billet(billet_id: int, billet_update: BilletUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Modifier un billet - Gestionnaires et Admins peuvent modifier, Agents seulement les leurs"""
    db_billet = db.query(BilletModel).filter(BilletModel.id == billet_id).first()
    if not db_billet:
        raise HTTPException(status_code=404, detail="Billet non trouvé")
    
    # Les agents ne peuvent modifier que leurs propres billets
    if hasattr(current_user, 'role') and current_user.role == 'agent':
        if db_billet.agent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que vos propres billets")
    
    update_data = billet_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_billet, field, value)
    
    db.commit()
    db.refresh(db_billet)
    return db_billet

@router.delete("/{billet_id}")
def delete_billet(billet_id: int, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_billet = db.query(BilletModel).filter(BilletModel.id == billet_id).first()
    if not db_billet:
        raise HTTPException(status_code=404, detail="Billet non trouvé")
    
    db.delete(db_billet)
    db.commit()
    return {"message": "Billet supprimé avec succès"}