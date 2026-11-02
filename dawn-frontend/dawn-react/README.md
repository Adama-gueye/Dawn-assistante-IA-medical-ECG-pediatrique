# DAWN — Frontend (React / Create React App)

Interface web de l'assistant médical DAWN, pour les **médecins** et l'**administrateur**.
Elle communique avec l'API FastAPI (`dawn-backend`) : le backend doit être démarré.

## Démarrer

```bash
npm install
cp .env.example .env     # REACT_APP_API_URL (par défaut http://localhost:8000)
npm start
```

Ouvre http://localhost:3000. Connexion avec un compte existant : l'administrateur est créé
par `python seed_admin.py` côté backend, les médecins sont créés par l'administrateur.

## Build de production

```bash
npm run build
```

## Fonctionnalités

- **Médecin** : tableau de bord et activité du mois (sélecteur de mois), dossiers patients
  (créer, modifier, supprimer), sessions de chat avec DAWN (texte, ECG WFDB `.hea`+`.dat`,
  CSV de test), profil et changement de mot de passe.
- **Chat** : une session est créée au premier message et nommée automatiquement d'après le sujet ;
  son titre est modifiable (clic) ; la session peut être supprimée.
- **Administrateur** : création et activation/désactivation des comptes médecins, statistiques
  d'usage par mois.

## Structure

```
src/
  api/          # client HTTP (jeton JWT en localStorage) et appels par domaine
  context/      # état global (useReducer), actions, modale de confirmation
  components/   # carte de réponse IA, graphiques en barres, sélecteur de mois, toasts
  pages/
    login/  doctor/  chat/  admin/
  utils/        # helpers (âge, dates) et mise en forme des messages (HTML échappé)
  styles/global.css
```

## Notes

- Les réponses du modèle sont **échappées** avant affichage (seul le gras `**…**` et les sauts de ligne
  sont interprétés).
- Le jeton JWT est conservé dans `localStorage` ; une réponse 401 vide la session locale.
