
import os
from urllib.request import urlopen
import speech_recognition as sr
import pyttsx3
import subprocess
from huggingface_hub import InferenceClient
from dotenv import load_dotenv  
import pygame


# Charger les variables d'environnement du fichier .env
load_dotenv()
pygame.mixer.init()


# Instanciation du client OpenAI avec la clé API
HUGGING_FACE_API_KEY = os.getenv('HUGGING_FACE_API_KEY')

def jouer_son(string):
    pygame.mixer.music.load(string)  # Charger le fichier audio
    pygame.mixer.music.play()  # Jouer le fichier audio


# Initialisation du moteur vocal
def assistant_voix(sortie):
    if sortie != None:
        voix = pyttsx3.init()
        print("A.I : " + sortie)
        voix.say(sortie)
        voix.runAndWait()

# Vérification de la connexion internet
def internet():
    try:
        urlopen('https://www.google.com', timeout=1)
        print("Connecté")
        return True
    except:
        print("Déconnecté")
        return False

# Reconnaissance vocale avec gestion des erreurs appropriées
def reconnaissance():
    r = sr.Recognizer()
    r.energy_threshold = 4000
    pas_compris = "Désolé, je n'ai pas compris."
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = 0.7
        jouer_son("parler.wav")  # Jouer le son pour indiquer que l'utilisateur peut parler
        
        print("Vous pouvez parler maintenant...")  # Message facultatif pour le débogage
        audio = r.listen(source)
        jouer_son("envoi.wav")  # Jouer le son pour indiquer que l'utilisateur peut parler

        if internet():
            try:
                vocal = r.recognize_google(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                assistant_voix(pas_compris)
            except sr.RequestError as e:
                assistant_voix(f"Erreur de service Google: {e}")
        else:
            try:
                vocal = r.recognize_sphinx(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                assistant_voix(pas_compris)

# Fonction pour ouvrir des applications
def application(entree):
    if entree != None:
        dico_apps = {
            "note": ["notepad", "note pad"],
            "sublime": ["sublime", "sublime texte"],
            "obs": ["obs", "obs capture", "capture l'écran"],
        }
        fini = False
        while not fini:
            for x in dico_apps["note"]:
                if x in entree.lower():
                    assistant_voix("Ouverture de Notepad.")
                    subprocess.Popen('C:\\Windows\\System32\\notepad.exe')
                    fini = True
            for x in dico_apps["sublime"]:
                if x in entree.lower():
                    assistant_voix("Ouverture de Sublime Text.")
                    subprocess.Popen('C:\\Program Files\\Sublime Text 3\\sublime_text.exe')
                    fini = True
            for x in dico_apps["obs"]:
                if x in entree.lower():
                    assistant_voix("Ouverture de OBS.")
                    subprocess.Popen('C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe')
                    fini = True
            fini = True


# Fonction pour exécuter des scripts externes
def executer_script(nom_script):
    def run_script(script):
        """ Fonction interne pour exécuter un script avec gestion des erreurs """
        try:
            subprocess.run(['python', script], check=True)
            assistant_voix(f"Le script {script} a été exécuté avec succès.")
            return True  # Script exécuté avec succès
        except subprocess.CalledProcessError:
            # Ne pas vocaliser l'erreur technique, juste un message simple
            assistant_voix(f"Il y a eu un problème lors de l'exécution du script {script}.")
            return False  # Erreur lors de l'exécution
        except FileNotFoundError:
            return False  # Le fichier n'a pas été trouvé

    # Première tentative avec le nom original
    if run_script(nom_script):
        return  # Script exécuté avec succès, on ne continue pas

    # Si le fichier n'existe pas, on remplace les espaces par des underscores et réessaye
    script_with_underscores = nom_script.replace(" ", "_")
    assistant_voix(f"Le script {nom_script} est introuvable. Essai avec {script_with_underscores} après correction.")
    
    # Deuxième tentative avec des underscores
    if not run_script(script_with_underscores):
        assistant_voix(f"Le script {script_with_underscores} est également introuvable.")

    

# Fonction pour envoyer un prompt à l'API Hugging Face et récupérer la réponse
def envoyer_prompt_huggingface(prompt):
    client = InferenceClient(
        token=HUGGING_FACE_API_KEY,
    )

    try:
        # Utiliser le modèle pour répondre au prompt donné par l'utilisateur
        response = client.chat_completion(
            model="microsoft/Phi-3-mini-4k-instruct",  # Le modèle utilisé
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Extraire la réponse du modèle
        generated_text = response.choices[0].message['content']
        assistant_voix(generated_text)  # L'assistant vocalise la réponse
        return 
    except Exception as e:
        assistant_voix(f"Erreur lors de l'appel à l'API Hugging Face : {e}")
        print(f"Erreur lors de l'appel à l'API Hugging Face : {e}")

def main():
    assistant_voix("Bonjour monsieur, je suis votre assistant de bureau. Dîtes 'bonjour' pour activer mes services.")
    trigger_word = "bonjour"  # Le mot clé pour activer l'assistant
    actif = False  # Le programme ne répond qu'une fois activé
    fermer = ["arrête-toi", "tais-toi"]
    ouvrir = ["ouvre", "ouvrir"]
    script = ["exécute le script", "lance le script", "exécute le programme", "lance le programme"] 
    ia_expressions = ["dis-moi", "donne-moi"]  # Expressions pour l'IA


    while True:
        entree = reconnaissance()  # On écoute l'utilisateur
        if entree:
            # Activation de l'assistant seulement après avoir dit le mot clé
            if not actif and trigger_word in entree.lower():
                assistant_voix("Activation réussie, comment puis-je vous aider ?")
                actif = True  # L'assistant est maintenant activé
            elif actif:
                # Si l'assistant est activé, traiter les autres commandes
                for x in fermer:
                    if x in entree.lower():
                        assistant_voix("À bientôt monsieur.")
                        actif = False  # Désactivation après avoir dit "arrête-toi"
                        break
                for x in ouvrir:
                    if x in entree.lower():
                        application(entree)
                        break
                for x in script:
                    if x in entree.lower():
                        script_name = entree.lower().replace(x, "").strip()
                        if script_name:
                            script_name = script_name + ".py"  # Ajouter l'extension .py au nom du script
                            executer_script(script_name)
                        break
                for x in ia_expressions:
                    if x in entree.lower():  # Vérifie si l'une des expressions IA est trouvée
                        prompt = entree.lower().replace(x, "").strip()  # Extrait le prompt après l'expression
                        envoyer_prompt_huggingface(prompt)  # Appelle l'IA avec le prompt
                        break

# Démarrage du programme
if __name__ == '__main__':
    main()
