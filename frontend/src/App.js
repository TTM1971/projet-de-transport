import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/home';
import Login from './pages/login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import BusList from './pages/BusList';
import LigneList from './pages/LigneList';
import DestinationList from './pages/DestinationList';
import UserList from './pages/UserList';
import BilletList from './pages/BilletList';
import SuiviFlotte from './pages/SuiviFlotte';
import SuiviMaintenance from './pages/SuiviMaintenance';
import VenteBillet from './pages/VenteBillet';
import GestionDeparts from './pages/GestionDeparts';
import GestionChauffeurs from './pages/GestionChauffeurs';
import BusDetails from './pages/BusDetails';
import AssignationChauffeurs from './pages/AssignationChauffeurs';
import BusMaintenanceDetail from './pages/BusMaintenanceDetail';
import BusEnServiceDetail from './pages/BusEnServiceDetail';
import InterventionsEnCoursDetail from './pages/InterventionsEnCoursDetail';
import ChiffreAffairesDetail from './pages/ChiffreAffairesDetail';
import BilletsDetail from './pages/BilletsDetail';
import TrajetsJourDetail from './pages/TrajetsJourDetail';
import AgentDeparts from './pages/AgentDeparts';
import UserApproval from './pages/UserApproval';
import GenerateDeparts from './pages/GenerateDeparts';
import ChauffeurPlanning from './pages/ChauffeurPlanning';
import ChauffeurEspace from './pages/ChauffeurEspace';
import HorairesEquipe from './pages/HorairesEquipe';
import VillesAdmin from './pages/VillesAdmin';
import DashboardVille from './pages/DashboardVille';

function defaultHomeForRole(role) {
  if (role === 'agent') return '/vente';
  if (role === 'chauffeur') return '/espace-chauffeur';
  return '/dashboard';
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Router>
      {user && <Navbar />}
      <div className={`app-content ${user ? 'with-shell' : ''}`}>
        <Routes>
          <Route path="/login" element={user ? <Navigate to={defaultHomeForRole(user.role)} replace /> : <Login />} />
          <Route path="/register" element={user ? <Navigate to={defaultHomeForRole(user.role)} replace /> : <Register />} />
          <Route path="/" element={<Navigate to={user ? defaultHomeForRole(user.role) : "/login"} replace />} />
          
          {/* Routes protégées par rôle */}
          <Route path="/dashboard" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire', 'maintenance', 'agent']} permission="dashboard">
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/vente" element={
            <ProtectedRoute allowedRoles={['admin', 'agent']} permission="vente">
              <VenteBillet />
            </ProtectedRoute>
          } />
          
          <Route path="/bus" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']} permission="bus">
              <BusList />
            </ProtectedRoute>
          } />
          
          <Route path="/bus/:busId" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire', 'maintenance']}>
              <BusDetails />
            </ProtectedRoute>
          } />
          
          <Route path="/bus/:busId/chauffeurs" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']}>
              <AssignationChauffeurs />
            </ProtectedRoute>
          } />
          
          <Route path="/lignes" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']} permission="lignes">
              <LigneList />
            </ProtectedRoute>
          } />
          
          <Route path="/destinations" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']} permission="destinations">
              <DestinationList />
            </ProtectedRoute>
          } />
          
          <Route path="/departs" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire', 'agent']} permission="departs">
              <GestionDeparts />
            </ProtectedRoute>
          } />
          
          <Route path="/departs/generate" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']} permission="departs">
              <GenerateDeparts />
            </ProtectedRoute>
          } />
          
          <Route path="/chauffeurs" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']} permission="chauffeurs">
              <GestionChauffeurs />
            </ProtectedRoute>
          } />

          <Route path="/chauffeurs/:chauffeurId/planning" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']} permission="chauffeurs">
              <ChauffeurPlanning />
            </ProtectedRoute>
          } />

          <Route path="/horaires-equipe" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']} permission="horaires_equipe">
              <HorairesEquipe />
            </ProtectedRoute>
          } />

          <Route path="/villes" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <VillesAdmin />
            </ProtectedRoute>
          } />

          <Route path="/dashboard/ville/:ville" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <DashboardVille />
            </ProtectedRoute>
          } />

          <Route path="/espace-chauffeur" element={
            <ProtectedRoute allowedRoles={['chauffeur']} permission="espace_chauffeur">
              <ChauffeurEspace />
            </ProtectedRoute>
          } />
          
          <Route path="/billets" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire', 'agent']} permission="billets_read">
              <BilletList />
            </ProtectedRoute>
          } />
          
          {/* Route pour consulter les départs (lecture seule pour les agents) */}
          <Route path="/departs-consultation" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire', 'agent']} permission="departs_read">
              <GestionDeparts />
            </ProtectedRoute>
          } />
          
          <Route path="/suivi-flotte" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire', 'maintenance']} permission="flotte">
              <SuiviFlotte />
            </ProtectedRoute>
          } />
          
          <Route path="/maintenance" element={
            <ProtectedRoute allowedRoles={['admin', 'maintenance']} permission="maintenance">
              <SuiviMaintenance />
            </ProtectedRoute>
          } />
          
          <Route path="/users" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']}>
              <UserList />
            </ProtectedRoute>
          } />
          
          <Route path="/users/approval" element={
            <ProtectedRoute allowedRoles={['admin', 'gestionnaire']}>
              <UserApproval />
            </ProtectedRoute>
          } />
          
          {/* Routes pour les détails du tableau de bord maintenance */}
          <Route path="/dashboard/maintenance/bus" element={
            <ProtectedRoute allowedRoles={['admin', 'maintenance']}>
              <BusMaintenanceDetail />
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard/maintenance/service" element={
            <ProtectedRoute allowedRoles={['admin', 'maintenance', 'gestionnaire']}>
              <BusEnServiceDetail />
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard/maintenance/interventions" element={
            <ProtectedRoute allowedRoles={['admin', 'maintenance']}>
              <InterventionsEnCoursDetail />
            </ProtectedRoute>
          } />
          
          {/* Routes pour les détails du tableau de bord admin */}
          <Route path="/dashboard/details/ca" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <ChiffreAffairesDetail />
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard/details/billets" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <BilletsDetail />
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard/details/trajets/:date" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <TrajetsJourDetail />
            </ProtectedRoute>
          } />
          
          {/* Route pour les départs disponibles pour l'agent */}
          <Route path="/agent/departs" element={
            <ProtectedRoute allowedRoles={['agent', 'admin']}>
              <AgentDeparts />
            </ProtectedRoute>
          } />
          
          <Route path="/home" element={<Home />} />
        </Routes>
      </div>
    </Router>
  );
}

function App() {
  return <AppRoutes />;
}

export default App;
