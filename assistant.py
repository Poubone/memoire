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
import re
from pystray import Icon, MenuItem, Menu
from PIL import Image
import sys


# Charger les variables d'environnement du fichier .env
load_dotenv()
pygame.mixer.init()

# Instanciation du client Hugging Face avec la clé API
HUGGING_FACE_API_KEY = os.getenv('HUGGING_FACE_API_KEY')
URL_SERVEUR = os.getenv('URL_SERVEUR')
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH')
IP_SERVEUR = os.getenv('IP_SERVEUR')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')

# URL de l'API pour récupérer les pull requests
url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls'

# En-têtes pour l'authentification
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# Variable globale pour contrôler l'état du thread de ping
ping_active = False

# Ajout d'un verrou pour les appels à pyttsx3 (le moteur vocal)
voice_lock = threading.Lock()

def quit_app(icon, item):
    """Quitte l'application proprement."""
    print("Fermeture de l'application.")
    icon.stop()
    sys.exit()

def create_image():
    """Créer l'icône (remplacez avec votre propre icône)."""
    return Image.open("icon.ico")

# Fonction pour démarrer l'icône dans la barre des tâches
def start_icon():
    menu = Menu(MenuItem('Quitter', quit_app))
    icon = Icon("MonApp", create_image(), "Compilotte", menu)
    icon.run()  # Démarre l'icône dans la barre des tâches

def jouer_son(string):
    pygame.mixer.music.load(string)  # Charger le fichier audio
    pygame.mixer.music.play()  # Jouer le fichier audio

# Initialisation du moteur vocal avec gestion des threads COM et utilisation du verrou
def assistant_voice(output):
    if output != None:
        with voice_lock:  # Protéger l'accès au moteur vocal avec un verrou
            pythoncom.CoInitialize()  # Initialiser COM dans le thread secondaire (uniquement sous Windows)
            voice = pyttsx3.init()
            print("A.I : " + output)
            voice.say(output)
            voice.runAndWait()

# Vérification de la connexion internet
def internet():
    try:
        urlopen('https://www.google.com', timeout=1)
        print("Connected")
        return True
    except:
        print("Disconnected")
        return False


# Fonction pour ping l'URL
def ping_server():
    global ping_active
    while ping_active:
        try:
            ping_command = get_ping_command()
            output = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if output.returncode != 0:    
                assistant_voice("Le serveur est down")
                stop_server_verification()
            else:
                assistant_voice("Le serveur est up")
                check_server_in_background()
        except Exception as e:
            assistant_voice(f"Erreur lors du ping : {e}")
        
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
def check_server_in_background():
    global ping_active
    if not ping_active:
        ping_active = True  # Activer le thread de ping
        # Créer un thread séparé pour exécuter le ping en arrière-plan
        thread = threading.Thread(target=ping_server)
        thread.daemon = True  # Permet au thread de s'arrêter quand le programme principal se termine
        thread.start()
        assistant_voice("La vérification du serveur a commencé.")
    else:
        assistant_voice("La vérification du serveur est déjà en cours.")

# Fonction pour arrêter la vérification du serveur
def stop_server_verification():
    global ping_active
    if ping_active:
        ping_active = False  # Désactiver le thread de ping
        assistant_voice("La vérification du serveur a été arrêtée.")
    else:
        assistant_voice("La vérification du serveur n'est pas en cours.")

def start_apache():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print((IP_SERVEUR))

        client.connect(hostname=IP_SERVEUR, username="memoire", key_filename=SSH_KEY_PATH)
        assistant_voice('Connexion à la VM réussie')

        command = "sudo systemctl start apache2"

        stdin, stdout, stderr = client.exec_command(command)
        stdout.channel.recv_exit_status()

        stdin.write('\n')
        stdin.flush()

        print(stdout.read().decode())
        print(stderr.read().decode())
        assistant_voice("Apache a été démarré avec succès")


    except Exception as e:
        assistant_voice(f"Erreur de connexion SSH ou de commande : {e}")
    finally:
        client.close()

def restart_apache():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=IP_SERVEUR, username="memoire", key_filename="C:/Users/gabin/.ssh/id_rsa")
        assistant_voice('Connexion à la VM réussie')

        command = "sudo systemctl restart apache2"

        stdin, stdout, stderr = client.exec_command(command)
        stdout.channel.recv_exit_status()

        stdin.write('\n')
        stdin.flush()

        print(stdout.read().decode())
        print(stderr.read().decode())
        assistant_voice("Apache a été redémarré avec succès")


    except Exception as e:
        assistant_voice(f"Erreur de connexion SSH ou de commande : {e}")
    finally:
        client.close()

def get_cpu_load():
    query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    
    response = requests.get(f"{URL_SERVEUR}:9090/api/v1/query", params={"query": query})

    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'success':
            cpu_usage = int(float(result['data']['result'][0]['value'][1]))
            assistant_voice(f"La charge du CPU est actuellement de {cpu_usage} pourcent")
        else:
            assistant_voice("Erreur lors de la requête Prometheus:")
            print(result)
    else:
        print("Erreur lors de la connexion à Prometheus")

def get_memory_load():
    query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
    
    response = requests.get(f"{URL_SERVEUR}:9090/api/v1/query", params={"query": query})

    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'success':
            cpu_usage = int(float(result['data']['result'][0]['value'][1]))
            assistant_voice(f"La mémoire est actuellement utilisée à {cpu_usage} pourcent")
        else:
            assistant_voice("Erreur lors de la requête Prometheus:")
            print(result)
    else:
        print("Erreur lors de la connexion à Prometheus")

def check_apache_status():
    try:
        assistant_voice('Connexion à la VM en cours')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=IP_SERVEUR, username="memoire", key_filename="C:/Users/gabin/.ssh/id_rsa")
        assistant_voice('Connexion à la VM réussie')

        stdin, stdout, stderr = client.exec_command("systemctl is-active apache2")
        status = stdout.read().decode().strip()

        print(status)

        if status == "active":
            assistant_voice("Le serveur Apache est opérationnel")
        else:
            assistant_voice("Le serveur Apache est hors service, je vais récupérer les log.")

            stdin, stdout, stderr = client.exec_command("sudo tail -n 10 /var/log/apache2/error.log")
            error_logs = stdout.readlines()

            assistant_voice("Voici les derniers log d'erreur")
            
            f = open("logs.txt", "w")

            for log in error_logs:
                f.write(log.strip())
                print(log.strip())
                
            f.close()

            
    except Exception as e:
        assistant_voice(f"Erreur de connexion SSH ou de commande : {e}")
    finally:
        client.close()
        assistant_voice("Fin de la connexion à la VM")




# Reconnaissance vocale avec gestion des erreurs appropriées
def reconnaissance(active):
    r = sr.Recognizer()
    r.energy_threshold = 4000
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = 0.7
        
        # Si l'assistant est activé, jouer les sons
        if active:
            jouer_son("parler.wav")  # Jouer le son pour indiquer que l'utilisateur peut parler
            print("Vous pouvez parler maintenant...")  # Message facultatif pour le débogage
            
        audio = r.listen(source)
        
        # Si l'assistant est activé, jouer le son d'envoi
        if active:
            jouer_son("envoi.wav")  # Jouer le son après l'enregistrement de la commande

        if internet():
            try:
                vocal = r.recognize_google(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                if active:  # Si l'assistant est activé, seulement alors afficher ce message
                    assistant_voice("Désolé, je n'ai pas compris.")
            except sr.RequestError as e:
                if active:
                    assistant_voice(f"Erreur de service Google: {e}")
        else:
            try:
                vocal = r.recognize_sphinx(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                if active:
                    assistant_voice("Désolé, je n'ai pas compris.")
                    
                    
##### FONCTIONS SUPPLÉMENTAIRES #####

# Fonction pour ouvrir des applications
def application(input):
    if input != None:
        dico_apps = {
            "note": ["notepad", "note pad"],
            "sublime": ["sublime", "sublime texte"],
            "obs": ["obs", "obs capture", "capture l'écran"],
        }
        fini = False
        while not fini:
            for x in dico_apps["note"]:
                if x in input.lower():
                    assistant_voice("Ouverture de Notepad.")
                    subprocess.Popen('C:\\Windows\\System32\\notepad.exe')
                    fini = True
            for x in dico_apps["sublime"]:
                if x in input.lower():
                    assistant_voice("Ouverture de Sublime Text.")
                    subprocess.Popen('C:\\Program Files\\Sublime Text 3\\sublime_text.exe')
                    fini = True
            for x in dico_apps["obs"]:
                if x in input.lower():
                    assistant_voice("Ouverture de OBS.")
                    subprocess.Popen('C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe')
                    fini = True
            fini = True

# Fonction pour exécuter des scripts externes
def execute_script(nom_script):
    def run_script(script):
        try:
            subprocess.run(['python', script], check=True)
            assistant_voice(f"Le script {script} a été exécuté avec succès.")
            return True  # Script exécuté avec succès
        except subprocess.CalledProcessError:
            # Ne pas vocaliser l'erreur technique, juste un message simple
            assistant_voice(f"Il y a eu un problème lors de l'exécution du script {script}.")
            return False  # Erreur lors de l'exécution
        except FileNotFoundError:
            return False  # Le fichier n'a pas été trouvé

    # Première tentative avec le nom original
    if run_script(nom_script):
        return  # Script exécuté avec succès, on ne continue pas

    # Si le fichier n'existe pas, on remplace les espaces par des underscores et réessaye
    script_with_underscores = nom_script.replace(" ", "_")
    assistant_voice(f"Le script {nom_script} est introuvable. Essai avec {script_with_underscores} après correction.")
    
    # Deuxième tentative avec des underscores
    if not run_script(script_with_underscores):
        assistant_voice(f"Le script {script_with_underscores} est également introuvable.")

# Fonction pour envoyer un prompt à l'API Hugging Face et récupérer la réponse
def send_prompt_huggingface(prompt):
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
        assistant_voice(generated_text)  # L'assistant vocalise la réponse
        return 
    except Exception as e:
        assistant_voice(f"Erreur lors de l'appel à l'API Hugging Face : {e}")
        print(f"Erreur lors de l'appel à l'API Hugging Face : {e}")


def analyse_logs():
    client = InferenceClient(token=HUGGING_FACE_API_KEY)
    f = open("logs.txt", "r")

    try:
        response = client.chat_completion(
            model="microsoft/Phi-3-mini-4k-instruct",  # Le modèle utilisé
            messages=[{"role": "user", "content": "Analyse les logs et donne-moi les possibles solutions :"+f.read()}],
            max_tokens=500
        )
        generated_text = response.choices[0].message['content']
        assistant_voice(generated_text)  
        return 
    except Exception as e:
        assistant_voice(f"Erreur lors de l'appel à l'API Hugging Face : {e}")
        print(f"Erreur lors de l'appel à l'API Hugging Face : {e}")

def extraire_nombre(texte):
    # Vérifie si "un" est présent dans le texte
    if "un" in texte.lower():
        return 1
    # Recherche un nombre dans le texte
    match = re.search(r'\d+', texte)
    # Retourne le nombre trouvé ou None si aucun nombre n'est présent
    return int(match.group()) if match else None

def git_interaction(): 
    pull_requests = get_pull_requests()

    if not pull_requests:
        assistant_voice(f"Aucune pull request trouvée.")
        print(f"Aucune pull request trouvée.")
        return
    pr_numbers = len(pull_requests)
    message_pull_request = f"Il y as {pr_numbers} nouvelles pull request,      "
    # Afficher les pull requests avec leur index
    for index, pr in enumerate(pull_requests):
        message_pull_request += f"[Pull request numéro {index + 1}] : {pr['title']}"

    assistant_voice(message_pull_request)
    print(message_pull_request)

def get_pull_requests():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur lors de la récupération des pull requests : {response.status_code} {response.text}")
        return []

def get_pull_request_by_number(number):
    pull_requests = get_pull_requests()
    if number >= len(pull_requests):  # Vérifie si l'index est valide
        return False
    return pull_requests[number]
    
def check_mergeable(pr):
    mergeable_url = f"{url}/{pr}"
    response = requests.get(mergeable_url, headers=headers)
    if response.status_code == 200:
        return response.json().get('mergeable')
    return False

def merge_pull_request(entree):
    number = extraire_nombre(entree)
    if number == None:
        print(f"Indiquez un index de pull request.")
        assistant_voice(f"Indiquez un index de pull request.")
        return
    pull_request = get_pull_request_by_number(number - 1)
    if pull_request == False:
        print(f"L'index fournis ne correspond a aucune pull request.")
        assistant_voice(f"L'index fournis ne correspond a aucune pull request.")
        return
    is_mergable = check_mergeable(pull_request["number"])
    if is_mergable == True:
        merge_url = f"{pull_request['url']}/merge"
        response = requests.put(merge_url, headers=headers)
        if response.status_code == 200:
            print(f"Pull request #{pull_request['number']} fusionnée avec succès.")
            assistant_voice(f"Pull request #{pull_request['number']} fusionnée avec succès.")
        else:
            print(f"Erreur lors de la fusion de la pull request #{pull_request['number']} : {response.status_code} {response.text}")
            assistant_voice(f"Erreur lors de la fusion de la pull request #{pull_request['number']}")
    else:
        print(f"Cette pull request n'est pas fusionnable avec main ou n'existe pas.")
        assistant_voice(f"Cette pull request n'est pas fusionnable avec main ou n'existe pas.")

def check_mergeable_interaction(entree):
    number = extraire_nombre(entree)
    if number == None:
        print(f"Indiquez un index de pull request.")
        assistant_voice(f"Indiquez un index de pull request.")
        return
    pull_request = get_pull_request_by_number(number - 1)
    if pull_request == False:
        print(f"L'index fournis ne correspond a aucune pull request.")
        assistant_voice(f"L'index fournis ne correspond a aucune pull request.")
        return
    is_mergable = check_mergeable(pull_request["number"])
    if is_mergable == True:
         print(f"Cette pull request est fusionnable avec main.")
         assistant_voice(f"Cette pull request est fusionnable avec main.")
    else:
        print(f"Cette pull request n'est pas fusionnable avec main ou n'existe pas.")
        assistant_voice(f"Cette pull request n'est pas fusionnable avec main ou n'existe pas.")

def main():
    assistant_voice("Dîtes 'bonjour' pour activer mes services.")
    trigger_word = "bonjour"  # Le mot clé pour activer l'assistant
    active = False  # Le programme ne répond qu'une fois activé
    close = ["arrête-toi"]
    open = ["ouvre", "ouvrir"]
    script = ["exécute le script", "lance le script", "exécute le programme", "lance le programme"] 
    ia_expressions = ["dis-moi", "donne-moi"] 
    state_server_start = ["vérifie l'état du serveur", "vérifier l'état du serveur"]  
    state_server_off = ["arrête de vérifier l'état du serveur", "arrête de ping le serveur"]  
    start_command_server = ["lance apache", "lance le serveur web"]
    restart_command_server = ["redémarre apache", "redémarre le serveur web"]  
    cpu_load = ["quelle est la charge CPU", "quelle est la charge du processeur"]
    memory_load = ["quelle est la charge mémoire"]
    apache_ok = ["vérifie si le serveur apache est ok", "est-ce que le serveur apache tourne correctement"]
    ia_answer_logs = ["analyse les logs"]
    askPr = ["montre-moi les pull request", "y as t-il de nouvelles pull request sur mon projet"]
    mergePr = ["peux-tu fusionner", "fusionner"]
    isMergeablePr = ["fusionnable", "réunir", "combinable", "combiner"]

    
    while True:
        entree = reconnaissance(active)  # On écoute l'utilisateur
        if entree:
            # Activation de l'assistant seulement après avoir dit le mot clé
            if not active and trigger_word in entree.lower():
                assistant_voice("Activation réussie, comment puis-je vous aider ?")
                active = True  # L'assistant est maintenant activé
            elif active:
                # Si l'assistant est activé, traiter les autres commandes
                for x in close:
                    if x in entree.lower():
                        assistant_voice("À bientôt monsieur.")
                        active = False  # Désactivation après avoir dit "arrête-toi"
                        break
                for x in open:
                    if x in entree.lower():
                        application(entree)
                        break
                for x in script:
                    if x in entree.lower():
                        script_name = entree.lower().replace(x, "").strip()
                        if script_name:
                            script_name = script_name + ".py"  # Ajouter l'extension .py au nom du script
                            execute_script(script_name)
                        break
                for x in ia_expressions:
                    if x in entree.lower():  # Vérifie si l'une des expressions IA est trouvée
                        prompt = entree.lower().replace(x, "").strip()  # Extrait le prompt après l'expression
                        send_prompt_huggingface(prompt)  # Appelle l'IA avec le prompt
                        break
                for x in state_server_start:
                    if x in entree.lower():
                        check_server_in_background()
                        break
                for x in state_server_off:
                    if x in entree.lower():
                        stop_server_verification()
                        break
                for x in start_command_server:
                    if x in entree.lower():
                        start_apache()
                        break
                for x in restart_command_server:
                    if x in entree.lower():
                        restart_apache()
                        break
                for x in cpu_load:
                    if x in entree.lower():
                        get_cpu_load()
                        break
                for x in memory_load:
                    if x in entree.lower():
                        get_memory_load()
                        break
                for x in apache_ok:
                    if x in entree.lower():
                        check_apache_status()
                        break
                for x in askPr:
                    if x in entree.lower():
                        git_interaction()
                        break
                for x in mergePr:
                    if x in entree.lower():
                        merge_pull_request(entree)
                        break
                for x in isMergeablePr:
                    if x in entree.lower():
                        check_mergeable_interaction(entree)
                        break
                for x in ia_answer_logs:
                    if x in entree.lower():
                        analyse_logs()
                        break
                    

# Lancer `main()` dans un thread séparé
threading.Thread(target=main, daemon=True).start()

# Lancer l'icône dans la barre des tâches
start_icon()
