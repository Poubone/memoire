import pyttsx3
from urllib.request import urlopen
import speech_recognition as sr

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


def recognition():
    r = sr.Recognizer()
    r.energy_threshold = 4000
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = 0.7

        print("Vous pouvez parler maintenant...")  
            
        audio = r.listen(source)
        
        if internet():
            try:
                vocal = r.recognize_google(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                assistant_voice("Désolé, je n'ai pas compris.")
            except sr.RequestError as e:
                assistant_voice(f"Erreur de service Google: {e}")
        else:
            try:
                vocal = r.recognize_sphinx(audio, language='fr-FR')
                print(vocal)
                return vocal
            except sr.UnknownValueError:
                assistant_voice("Désolé, je n'ai pas compris.")
                    
                    
def main():
    assistant_voice("Bonjour, je suis votre assistant vocal.")
    while True:
        input = recognition()  
        if input :
            assistant_voice(input)


if __name__ == '__main__':
    main()
