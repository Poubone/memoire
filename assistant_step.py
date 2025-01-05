import os
import pyttsx3
from urllib.request import urlopen
import speech_recognition as sr
import pygame
import subprocess
import threading
import platform
import time



pygame.mixer.init()

URL_SERVEUR = os.getenv('URL_SERVEUR')

def play_sound(string):
    pygame.mixer.music.load(string) 
    pygame.mixer.music.play()  

def assistant_voice(output):
    if output!= None:
        voice = pyttsx3.init()
        print("A.I : " + output)
        voice.say(output)
        voice.runAndWait()
     
def internet():
    try:
        urlopen('https://www.google.com', timeout=1)
        print("Connecté")
        return True
    except:
        print("Déconnecté")
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

def recognition(active):
    r = sr.Recognizer()
    r.energy_threshold = 4000
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = 0.7
        if active:
            play_sound("parler.wav")  
            print("Vous pouvez parler maintenant...")  
            
        audio = r.listen(source)
        
        if active: 
            play_sound("envoi.wav")  

        if internet():
            try:
                vocal = r.recognize_google(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                if active:  
                    assistant_voice("Désolé, je n'ai pas compris.")
            except sr.RequestError as e:
                if active:
                    assistant_voice(f"Erreur de service Google: {e}")
        else:
            try:
                vocal.recognize_sphinx(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                if active:
                    assistant_voice("Désolé, je n'ai pas compris.")
                    
                    
                    
def application(input):
    if input!= None:
        dico_apps = {
            "note": ["notepad", "note pad"],
            "sublime": ["sublime", "sublime texte"],
            "obs": ["obs", "obs capture", "capture l'écran"],
        }
        ended = False
        while not ended :
            for x in dico_apps["note"]:
                if x in input.lower():
                    assistant_voice("Ouverture de Notepad.")
                    subprocess.Popen('C:\\Windows\\System32\\notepad.exe')
                    ended  = True
            for x in dico_apps["sublime"]:
                if x in input.lower():
                    assistant_voice("Ouverture de Sublime Text.")
                    subprocess.Popen('C:\\Program Files\\Sublime Text 3\\sublime_text.exe')
                    ended = True
            for x in dico_apps["obs"]:
                if x in input.lower():
                    assistant_voice("Ouverture de OBS.")
                    subprocess.Popen('C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe')
                    ended = True
            ended = True       

def execute_script(script_name):
    def run_script(script):        
        try:
            subprocess.run(['python', script], check=True)
            assistant_voice(f"Le script {script} a été exécuté avec succès.")
            return True  
        except subprocess.CalledProcessError:
            assistant_voice(f"Il y a eu un problème lors de l'exécution du script {script}.")
            return False  
        except FileNotFoundError:
            return False  
    if run_script(script_name):
        return  
    script_with_underscores = script_name.replace(" ", "_")
    assistant_voice(f"Le script {script_name} est introuvable. Essai avec {script_with_underscores} après correction.")
    
    if not run_script(script_with_underscores):
        assistant_voice(f"Le script {script_with_underscores} est également introuvable.")
                    
def main():
    assistant_voice("Dîtes 'bonjour' pour activer mes services.")
    trigger_word = "bonjour"  
    close = ["arrête-toi"]
    open = ["ouvre", "ouvrir"]        
    script = ["exécute le script", "lance le script", "exécute le programme", "lance le programme"] 
    state_server_start = ["vérifie l'état du serveur", "vérifier l'état du serveur"]  
    state_server_off = ["arrête de vérifier l'état du serveur", "arrête de ping le serveur"]  

    active = False  
    while True:
        input = recognition(active) 
        if input:
            if not active and trigger_word in input.lower():
                assistant_voice("Activation réussie, comment puis-je vous aider ?")
                active = True  
            elif active :
                for x in close :
                    if x in input.lower():
                        assistant_voice("À bientôt monsieur.")
                        active = False  
                        break
                for x in open :
                    if x in input.lower():
                        application(input)
                        break       
                for x in script:
                    if x in input.lower():
                        script_name = input.lower().replace(x, "").strip()
                        if script_name:
                            script_name = script_name + ".py"  # Ajouter l'extension .py au nom du script
                            execute_script(script_name)
                        break
                for x in state_server_start:
                    if x in input.lower():
                        check_server_in_background()
                        break
                for x in state_server_off:
                    if x in input.lower():
                        stop_server_verification()
                        break


if __name__ == '__main__':
    main()
