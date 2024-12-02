
# Assistant Vocal en Python

Ce projet est un assistant vocal simple capable d'écouter des commandes, d'ouvrir des applications, de faire des recherches sur internet, et de répondre à certaines questions de base. Il se déclenche uniquement lorsque l'utilisateur dit "bonjour".

## Prérequis

Avant de pouvoir exécuter ce projet, vous devez installer Python et plusieurs bibliothèques nécessaires. Suivez les étapes ci-dessous pour configurer l'environnement.

### 1. Installer Python

Assurez-vous que Python 3.6 ou supérieur est installé sur votre machine. Vous pouvez le télécharger [ici](https://www.python.org/downloads/).

### 2. Cloner le projet

```bash
git clone https://github.com/votre-repo/assistant-vocal.git
cd assistant-vocal
```

### 3. Installer les dépendances

Utilisez `pip` pour installer les bibliothèques Python nécessaires. Exécutez la commande suivante dans le répertoire du projet :

```bash
pip install SpeechRecognition pyttsx3 huggingface-hub python-dotenv pygame pywin32
```

### 4. Installation des bibliothèques système requises

Certaines bibliothèques comme `pyttsx3` nécessitent des packages supplémentaires pour fonctionner, selon votre système d'exploitation.

#### Windows
- Vous n'avez rien à faire, toutes les dépendances seront installées via `pip`.

#### Linux
- Vous devrez installer des dépendances supplémentaires comme `espeak` et `ffmpeg` :

```bash
sudo apt-get install espeak ffmpeg libespeak1
```

#### macOS
- Vous pouvez installer `brew` pour gérer les dépendances :

```bash
brew install espeak
```

## Utilisation

Pour lancer l'assistant, exécutez simplement le fichier `assistant.py` 

```bash
python assistant.py
```

### Fonctionnalités disponibles

- **Activation via un mot-clé** : L'assistant ne répondra qu'après avoir entendu "bonjour".
- **Commandes disponibles** :
  - Ouvrir des applications (ex: Notepad, Sublime Text, OBS).
  - Demander quelque chose à l'IA.
  - Executer des scripts python.
  - Executer un ping sur une adresse IP.

### Arrêter l'assistant

Pour arrêter l'assistant, vous pouvez dire :
- "arrête-toi"
- "tais-toi"

## Dépendances

Voici les principales bibliothèques utilisées dans ce projet :

- `pyttsx3` : Pour la synthèse vocale.
- `SpeechRecognition` : Pour la reconnaissance vocale.
- `huggingface-hub` : Pour utiliser l'API GPT-3 d'OpenAI.
- `python-dotenv` : Pour charger les variables d'environnement à partir d'un fichier `.env`.
- `pygame` : Pour jouer des sons.
- `pywin32` : Pour exécuter des commandes système sur Windows.

### 5. Configuration de l'API OpenAI

Pour utiliser l'API d'Hugging Face, vous devez obtenir une clé d'API et la configurer dans un fichier `.env`. Créez un fichier `.env` à la racine du projet et ajoutez votre clé d'API comme suit :

HUGGING_FACE_API_KEY=YOUR_API_KEY
URL_SERVEUR=YOUR_URL
IP_SERVEUR=IP_DE_LA_VM
SSH_KEY_PATH=CHEMIN_DE_LA_CLE_SSH

(Au besoin, un fichier .env.example est fourni)

``

