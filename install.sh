#!/bin/bash

echo "🔧 Installation du module waveshare_epd..."

# Étape 1 : Créer le dossier lib/ si besoin
mkdir -p lib

# Étape 2 : Cloner le dépôt officiel Waveshare
echo "📥 Clonage du dépôt GitHub..."
git clone https://github.com/waveshare/e-Paper.git temp_epaper_repo

# Étape 3 : Copier uniquement la librairie utile
echo "📦 Copie de waveshare_epd..."
mv temp_epaper_repo/RaspberryPi_JetsonNano/python/lib/waveshare_epd lib/

# Étape 4 : Nettoyage
echo "🧹 Nettoyage..."
rm -rf temp_epaper_repo

# Étape 5 : Vérification
if [ -d "lib/waveshare_epd" ]; then
    echo "✅ Installation terminée avec succès !"
else
    echo "❌ Échec de l'installation. Vérifie le script."
    exit 1
fi