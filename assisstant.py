from urllib.request import urlopen
from translate import Translator
from random import choice
import speech_recognition as sr
import pyttsx3
import subprocess
import wolframalpha
import webbrowser
import wikipedia

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
        print(".... ")
        audio = r.listen(source)
        
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


# Fonction pour effectuer des recherches sur le net
def sur_le_net(entree):
    if entree != None:
        if "youtube" in entree.lower(): 
            indx = entree.lower().split().index("youtube") 
            recherche = entree.lower().split()[indx + 1:]
            if len(recherche) != 0:
                assistant_voix("Recherche sur YouTube.")
                webbrowser.open("http://www.youtube.com/results?search_query=" + "+".join(recherche), new=2)
        elif "wikipédia" in entree.lower(): 
            wikipedia.set_lang("fr")
            try:
                recherche = entree.lower().replace("cherche sur wikipédia", "")
                if len(recherche) != 0:
                    resultat = wikipedia.summary(recherche, sentences=1)
                    assistant_voix("Recherche sur Wikipédia.")
                    assistant_voix(resultat)
            except:
                assistant_voix("Désolé, aucune page trouvée.") 
        else: 
            if "google" in entree.lower():
                indx = entree.lower().split().index("google") 
                recherche = entree.lower().split()[indx + 1:]
                if len(recherche) != 0:
                    assistant_voix("Recherche sur Google.")
                    webbrowser.open("https://www.google.com/search?q=" + "+".join(recherche), new=2)
            elif "cherche" in entree.lower() or "recherche" in entree.lower():
                indx = entree.lower().split().index("cherche") 
                recherche = entree.lower().split()[indx + 1:]
                if len(recherche) != 0:
                    assistant_voix("Recherche par défaut.")
                    webbrowser.open("https://www.google.com/search?q=" + "+".join(recherche), new=2)

# Fonction principale modifiée avec un trigger word
def main():
    assistant_voix("Bonjour monsieur, je suis votre assistant de bureau. Dîtes 'bonjour' pour activer mes services.")
    trigger_word = "bonjour"  # Le mot clé pour activer l'assistant
    actif = False  # Le programme ne répond qu'une fois activé
    fermer = ["arrête-toi", "tais-toi"]
    ouvrir = ["ouvre", "ouvrir"]
    cherche = ["cherche sur youtube", "cherche sur google", "cherche sur wikipédia", "cherche"]

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
                for x in cherche:
                    if x in entree.lower():
                        sur_le_net(entree)
                        break

# Démarrage du programme
if __name__ == '__main__':
    main()