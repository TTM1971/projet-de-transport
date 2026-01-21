// Utility to translate database values to English for display
export const translateStatus = (status) => {
  const translations = {
    // Bus statuses
    'disponible': 'Available',
    'en_service': 'In Service',
    'en_maintenance': 'In Maintenance',
    'hors_service': 'Out of Service',
    
    // Driver statuses
    'actif': 'Active',
    'en_conge': 'On Leave',
    'conge': 'On Leave',
    'inactif': 'Inactive',
    'suspendu': 'Suspended',
    
    // Line statuses
    'active': 'Active',
    'inactive': 'Inactive',
    
    // Departure statuses
    'programme': 'Scheduled',
    'en_cours': 'In Progress',
    'termine': 'Completed',
    'annule': 'Cancelled',
    
    // Payment methods
    'espece': 'Cash',
    'mobile_money': 'Mobile Money',
    'mobile': 'Mobile Money',
    'carte': 'Card',
    
    // Intervention statuses
    'en_attente': 'Pending',
    'terminee': 'Completed',
    'annulee': 'Cancelled',
    
    // Ticket statuses
    'valide': 'Valid',
    'utilise': 'Used',
    'annule': 'Cancelled',
    'rembourse': 'Refunded',
    
    // Assignment types
    'jour': 'Day',
    'nuit': 'Night',
  };
  
  return translations[status] || status;
};

// Translate breakdown types
export const translateBreakdownType = (type) => {
  const translations = {
    'freinage': 'Braking',
    'pneus': 'Tires',
    'moteur': 'Engine',
    'électrique': 'Electrical',
    'electrique': 'Electrical',
    'climatisation': 'Air Conditioning',
    'carrosserie': 'Bodywork',
    'transmission': 'Transmission',
    'autre': 'Other',
  };
  
  return translations[type] || type;
};

// Translate severity levels
export const translateSeverity = (severity) => {
  const translations = {
    'mineure': 'Minor',
    'moyenne': 'Medium',
    'majeure': 'Major',
    'critique': 'Critical',
  };
  
  return translations[severity] || severity;
};

export const translateField = (field, value) => {
  if (field === 'statut' || field === 'status') {
    return translateStatus(value);
  }
  if (field === 'type_panne' || field === 'type_panne') {
    return translateBreakdownType(value);
  }
  if (field === 'gravite' || field === 'severity') {
    return translateSeverity(value);
  }
  if (field === 'mode_paiement' || field === 'payment_method') {
    return translateStatus(value); // Payment methods are also in translateStatus
  }
  return value;
};

// Main translation function that handles any database value
export const translate = (value, field = null) => {
  if (!value) return value;
  
  if (field) {
    return translateField(field, value);
  }
  
  // Try all translation functions
  const translated = translateStatus(value) || translateBreakdownType(value) || translateSeverity(value);
  return translated !== value ? translated : value;
};
