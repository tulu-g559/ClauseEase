import pyttsx3

def speak_text(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)  
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)  
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    text = input("Enter the text you want to speak: ") 
    speak_text(text)
