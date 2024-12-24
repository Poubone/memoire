import pyttsx3
from urllib.request import urlopen
import speech_recognition as sr
import pygame


pygame.mixer.init()



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
                    
def main():
    assistant_voice("Dîtes 'bonjour' pour activer mes services.")
    trigger_word = "bonjour"  
    close = ["arrête-toi"]

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


if __name__ == '__main__':
    main()
