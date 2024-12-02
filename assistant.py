import os
import platform
import threading
import time
from urllib.request import urlopen
import speech_recognition as sr
import pyttsx3
import subprocess
from huggingface_hub import InferenceClient
from dotenv import load_dotenv  
import pygame
import pythoncom
import paramiko
import requests


# Charger les variables d'environnement du fichier .env
load_dotenv()
pygame.mixer.init()

# Instanciation du client Hugging Face avec la clé API
HUGGING_FACE_API_KEY = os.getenv('HUGGING_FACE_API_KEY')
URL_SERVEUR = os.getenv('URL_SERVEUR')
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH')
IP_SERVEUR = os.getenv('IP_SERVEUR')


# Variable globale pour contrôler l'état du thread de ping
ping_active = False

# Ajout d'un verrou pour les appels à pyttsx3 (le moteur vocal)
voix_lock = threading.Lock()

def jouer_son(string):
    pygame.mixer.music.load(string)  # Charger le fichier audio
    pygame.mixer.music.play()  # Jouer le fichier audio

# Initialisation du moteur vocal avec gestion des threads COM et utilisation du verrou
def assistant_voix(sortie):
    if sortie != None:
        with voix_lock:  # Protéger l'accès au moteur vocal avec un verrou
            pythoncom.CoInitialize()  # Initialiser COM dans le thread secondaire (uniquement sous Windows)
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


# Fonction pour ping l'URL
def ping_serveur():
    global ping_active
    while ping_active:
        try:
            ping_command = get_ping_command()
            output = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if output.returncode != 0:    
                assistant_voix("Le serveur est down")
                arreter_verification_serveur()
            else:
                assistant_voix("Le serveur est up")
                arreter_verification_serveur()
        except Exception as e:
            assistant_voix(f"Erreur lors du ping : {e}")
        
        time.sleep(30)  # Attendre 30 secondes avant de réessayer

# Fonction pour adapter la commande de ping selon le système d'exploitation
def get_ping_command():
    system = platform.system()
    if system == "Windows":
        return ["ping", "-n", "1", URL_SERVEUR]
    elif system == "Linux" or system == "Darwin":  # macOS est "Darwin"
        return ["ping", "-c", "1", URL_SERVEUR]
    else:
        raise Exception(f"Système d'exploitation non pris en charge : {system}")


# Thread de vérification du serveur
def verifier_serveur_en_fond():
    global ping_active
    if not ping_active:
        ping_active = True  # Activer le thread de ping
        # Créer un thread séparé pour exécuter le ping en arrière-plan
        thread = threading.Thread(target=ping_serveur)
        thread.daemon = True  # Permet au thread de s'arrêter quand le programme principal se termine
        thread.start()
        assistant_voix("La vérification du serveur a commencé.")
    else:
        assistant_voix("La vérification du serveur est déjà en cours.")

# Fonction pour arrêter la vérification du serveur
def arreter_verification_serveur():
    global ping_active
    if ping_active:
        ping_active = False  # Désactiver le thread de ping
        assistant_voix("La vérification du serveur a été arrêtée.")
    else:
        assistant_voix("La vérification du serveur n'est pas en cours.")

def demarrer_apache():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=IP_SERVEUR, username="memoire", key_filename=SSH_KEY_PATH)
        assistant_voix('Connexion à la VM réussie')

        command = "sudo systemctl start apache2"

        stdin, stdout, stderr = client.exec_command(command)
        stdout.channel.recv_exit_status()

        stdin.write('\n')
        stdin.flush()

        print(stdout.read().decode())
        print(stderr.read().decode())
        assistant_voix("Apache a été démarré avec succès")


    except Exception as e:
        assistant_voix(f"Erreur de connexion SSH ou de commande : {e}")
    finally:
        client.close()

def redemarrer_apache():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=IP_SERVEUR, username="memoire", key_filename="C:/Users/gabin/.ssh/id_rsa")
        assistant_voix('Connexion à la VM réussie')

        command = "sudo systemctl restart apache2"

        stdin, stdout, stderr = client.exec_command(command)
        stdout.channel.recv_exit_status()

        stdin.write('\n')
        stdin.flush()

        print(stdout.read().decode())
        print(stderr.read().decode())
        assistant_voix("Apache a été redémarré avec succès")


    except Exception as e:
        assistant_voix(f"Erreur de connexion SSH ou de commande : {e}")
    finally:
        client.close()

def get_charge_cpu():
    query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    
    response = requests.get(f"{URL_SERVEUR}:9090/api/v1/query", params={"query": query})

    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'success':
            cpu_usage = int(float(result['data']['result'][0]['value'][1]))
            assistant_voix(f"La charge du CPU est actuellement de {cpu_usage} pourcent")
        else:
            assistant_voix("Erreur lors de la requête Prometheus:")
            print(result)
    else:
        print("Erreur lors de la connexion à Prometheus")

def get_charge_memoire():
    query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
    
    response = requests.get(f"{URL_SERVEUR}:9090/api/v1/query", params={"query": query})

    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'success':
            cpu_usage = int(float(result['data']['result'][0]['value'][1]))
            assistant_voix(f"La mémoire est actuellement utilisée à {cpu_usage} pourcent")
        else:
            assistant_voix("Erreur lors de la requête Prometheus:")
            print(result)
    else:
        print("Erreur lors de la connexion à Prometheus")

def check_apache_status():
    try:
        assistant_voix('Connexion à la VM en cours')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=IP_SERVEUR, username="memoire", key_filename="C:/Users/gabin/.ssh/id_rsa")
        assistant_voix('Connexion à la VM réussie')

        stdin, stdout, stderr = client.exec_command("systemctl is-active apache2")
        status = stdout.read().decode().strip()

        print(status)

        if status == "active":
            assistant_voix("Le serveur Apache est opérationnel")
        else:
            assistant_voix("Le serveur Apache est hors service, je vais récupérer les log.")

            stdin, stdout, stderr = client.exec_command("sudo tail -n 10 /var/log/apache2/error.log")
            error_logs = stdout.readlines()

            assistant_voix("Voici les derniers log d'erreur")
            
            for log in error_logs:
                print(log.strip())
    except Exception as e:
        assistant_voix(f"Erreur de connexion SSH ou de commande : {e}")
    finally:
        client.close()
        assistant_voix("Fin de la connexion à la VM")




# Reconnaissance vocale avec gestion des erreurs appropriées
def reconnaissance(actif):
    r = sr.Recognizer()
    r.energy_threshold = 4000
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = 0.7
        
        # Si l'assistant est activé, jouer les sons
        if actif:
            jouer_son("parler.wav")  # Jouer le son pour indiquer que l'utilisateur peut parler
            print("Vous pouvez parler maintenant...")  # Message facultatif pour le débogage
            
        audio = r.listen(source)
        
        # Si l'assistant est activé, jouer le son d'envoi
        if actif:
            jouer_son("envoi.wav")  # Jouer le son après l'enregistrement de la commande

        if internet():
            try:
                vocal = r.recognize_google(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                if actif:  # Si l'assistant est activé, seulement alors afficher ce message
                    assistant_voix("Désolé, je n'ai pas compris.")
            except sr.RequestError as e:
                if actif:
                    assistant_voix(f"Erreur de service Google: {e}")
        else:
            try:
                vocal = r.recognize_sphinx(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                if actif:
                    assistant_voix("Désolé, je n'ai pas compris.")
                    
                    
##### FONCTIONS SUPPLÉMENTAIRES #####

# Fonction pour ping l'URL
def ping_serveur():
    global ping_active
    while ping_active:
        try:
            ping_command = get_ping_command()
            output = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if output.returncode != 0:    
                assistant_voix("Le serveur est down")
        except Exception as e:
            assistant_voix(f"Erreur lors du ping : {e}")
        
        time.sleep(30)  # Attendre 30 secondes avant de réessayer

# Fonction pour adapter la commande de ping selon le système d'exploitation
def get_ping_command():
    system = platform.system()
    if system == "Windows":
        return ["ping", "-n", "1", URL_SERVEUR]
    elif system == "Linux" or system == "Darwin":  # macOS est "Darwin"
        return ["ping", "-c", "1", URL_SERVEUR]
    else:
        raise Exception(f"Système d'exploitation non pris en charge : {system}")

# Thread de vérification du serveur
def verifier_serveur_en_fond():
    global ping_active
    if not ping_active:
        ping_active = True  # Activer le thread de ping
        # Créer un thread séparé pour exécuter le ping en arrière-plan
        thread = threading.Thread(target=ping_serveur)
        thread.daemon = True  # Permet au thread de s'arrêter quand le programme principal se termine
        thread.start()
        assistant_voix("La vérification du serveur a commencé.")
    else:
        assistant_voix("La vérification du serveur est déjà en cours.")

# Fonction pour arrêter la vérification du serveur
def arreter_verification_serveur():
    global ping_active
    if ping_active:
        ping_active = False  # Désactiver le thread de ping
        assistant_voix("La vérification du serveur a été arrêtée.")
    else:
        assistant_voix("La vérification du serveur n'est pas en cours.")

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
    client = InferenceClient(token=HUGGING_FACE_API_KEY)

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
    assistant_voix("Dîtes 'bonjour' pour activer mes services.")
    trigger_word = "bonjour"  # Le mot clé pour activer l'assistant
    actif = False  # Le programme ne répond qu'une fois activé
    fermer = ["arrête-toi"]
    ouvrir = ["ouvre", "ouvrir"]
    script = ["exécute le script", "lance le script", "exécute le programme", "lance le programme"] 
    ia_expressions = ["dis-moi", "donne-moi"] 
    etat_serveur_start = ["vérifie l'état du serveur", "vérifier l'état du serveur"]  
    etat_serveur_off = ["arrête de vérifier l'état du serveur", "arrête de ping le serveur"]  
    demarrer_commande = ["lance apache", "lance le serveur web"]
    redemarrer_commande = ["redémarre apache", "redémarre le serveur web"]  
    charge_cpu = ["quelle est la charge CPU", "quelle est la charge du processeur"]
    charge_memoire = ["quelle est la charge mémoire"]
    apache_ok = ["vérifie si le serveur apache est ok", "est-ce que le serveur apache tourne correctement"]
    
    while True:
        entree = reconnaissance(actif)  # On écoute l'utilisateur
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
                for x in etat_serveur_start:
                    if x in entree.lower():
                        verifier_serveur_en_fond()
                        break
                for x in etat_serveur_off:
                    if x in entree.lower():
                        arreter_verification_serveur()
                        break
                for x in demarrer_commande:
                    if x in entree.lower():
                        demarrer_apache()
                        break
                for x in redemarrer_commande:
                    if x in entree.lower():
                        redemarrer_apache()
                        break
                for x in charge_cpu:
                    if x in entree.lower():
                        get_charge_cpu()
                        break
                for x in charge_memoire:
                    if x in entree.lower():
                        get_charge_memoire()
                        break
                for x in apache_ok:
                    if x in entree.lower():
                        check_apache_status()
                        break
                    

# Démarrage du programme
if __name__ == '__main__':
    main()
