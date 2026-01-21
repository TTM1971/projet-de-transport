// Utilitaire pour la conversion de devises et l'affichage des prix
// Taux de change EUR -> CAD (dollars canadiens)
const EUR_TO_CAD_RATE = 1.47; // Taux approximatif (à mettre à jour régulièrement)

/**
 * Convertit un montant en EUR vers CAD
 * @param {number} eur - Montant en euros
 * @returns {number} - Montant en dollars canadiens
 */
export const eurToCad = (eur) => {
  if (!eur || isNaN(eur)) return 0;
  return parseFloat(eur) * EUR_TO_CAD_RATE;
};

/**
 * Formate un montant en CAD avec le symbole $
 * @param {number} cad - Montant en dollars canadiens
 * @param {number} decimals - Nombre de décimales (par défaut 2)
 * @returns {string} - Montant formaté (ex: "$150.00 CAD")
 */
export const formatCad = (cad, decimals = 2) => {
  if (!cad || isNaN(cad)) return "$0.00 CAD";
  return `$${parseFloat(cad).toFixed(decimals)} CAD`;
};

/**
 * Convertit EUR vers CAD et formate le résultat
 * @param {number} eur - Montant en euros
 * @param {number} decimals - Nombre de décimales (par défaut 2)
 * @returns {string} - Montant formaté en CAD
 */
export const eurToCadFormatted = (eur, decimals = 2) => {
  return formatCad(eurToCad(eur), decimals);
};

/**
 * Formate un montant en EUR et le convertit en CAD pour l'affichage
 * @param {number} eur - Montant en euros
 * @param {number} decimals - Nombre de décimales (par défaut 2)
 * @returns {string} - Montant formaté en CAD (ex: "$150.00 CAD")
 */
export const formatPrice = (eur, decimals = 2) => {
  return eurToCadFormatted(eur, decimals);
};
