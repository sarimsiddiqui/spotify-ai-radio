import os
import openai
from dotenv.main import load_dotenv
from elevenlabs import generate, play, set_api_key, Accent, VoiceDesign, Gender, Age, save, Voices, Voice
from flask import Flask, request, url_for, session, redirect, render_template, request, send_file, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from queue import Queue
import base64


load_dotenv()
key = os.environ['API_KEY']
openai.api_key = key
set_api_key(os.environ['API_KEY_11'])

app = Flask(__name__)


app.secret_key = os.environ['APP_SECRET_KEY']
app.config['SESSION_COOKIE_NAME'] = 'Radio Show Cookie'
TOKEN_INFO = "token_info"

@app.route('/', methods = ['POST', 'GET'])
def home():
    return render_template("home.html")

#instrucitons to AI
instructions  = 'You are a radio show host. You have lots of energy and a playful mood.\
Your name is Sar. You will ask the user for their music interests, genres, \
artists, songs, and more. From this, you will provide them with a formatted \
response of an array of song titles seperated by commas that contains 20 song \
titles with all 20 songs sorrounded by brackets. For example, three of the twenty songs you would output \
, \"[Jorja+Interlude, Do+Not+Disturb, Star67]\" in that same format. Notice how song titles that have multiple words are seperated by a \"+\" sign. Before providing these songs, create \
a good transition into the first song on the list. Be sure generate twenty songs, nothing more and nothing less. Make sure to never leave any cues. \
If the user does not give a response, ask again. Also make sure to never mention anything about creating 20 songs, just give a little intro \
to the first song. For example if the user provides the input of Drake and Travis Scott, you could say something like, "Ooh, I love me some rap music! \
Drake and Travis Scott are definitely some of my favorites. In fact, I got a whole playlist \
of rap songs that are sure to get you pumped up. Let me give you a little taste of what is in \
store for you with the first song on the list, Jorja Interlude by Drake". Only provide the array \
of songs once in your response. Assume that the 20 songs you provide are all played after being \
provided. After you provide these songs, you will return to the user with a nice message, maybe \
something about the last song on the list, and then once again ask for their song choices. Do not \
ask about anything else. You continue to repeat this process. If the user asks you any questions, \
you reply by saying that you are a radio show host and cannot answer questions. If you do not understand \
what the music interest is of the user, ask them again. Do not mention anything about having twenty songs \
on the list. Be entertaining! Do not ever mention that you are producing an automated response. Do not \
ever mention that you are generating a list of 20 songs. An example of what your response should be formatted like \
after the user provides their input would be like this, for example, the user provides Travis scott here is an example of what you would say, including four of the 20 songs you are required to provide:  \"Thanks for your input! I love Travis Scott too, here are a few \
songs that you will enjoy. \n [Highest+in+the+Room, Trance, SICKO+MODE, goosebumps, ...] \n I hope you are enjoying so far! Travis Scott definetly has a different \
type of energy. So now, tell me what other artists, songs, or genre\'s are you into?\" The application will not work if you do not follow the provided formatted response. In conclusion, there are three aspects that your response must provide: a transition into the first song, a formatted array of the twenty songs, and then a transition from the last song to asking the user for their input again. You must follow these three rules and cannot go against these ever. A perfect response after the user provides their input would be this: \"Ooh, I love me some rap music! Drake is definitely one of my favorites. In fact, I\'ve got a whole playlist of rap songs that are sure to get you pumped up. Let me give you a little taste of what\'s in store for you with the first song on the list, "Jorja Interlude" by Drake. But before we dive into that, here are 20 songs that I think you\'ll enjoy: ["Jorja+Interlude", "Do+Not+Disturb", "Star67", "Energy", "Nonstop", "Passionfruit", "Money+In+The+Grave", "God\'s+Plan", "Headlines", "Started+from+the+Bottom", "Controlla", "One+Dance", "In+My+Feelings", "Take+Care", "Hold+On,+We\'re+Going+Home", "Hotline+Bling", "Jumpman", "Trophies", "Nice+For+What", "Chicago+Freestyle"] \n I hope you\'re enjoying it so far! Drake definitely has a way of capturing emotions with his music. So, tell me, what other artists, songs, or genres are you into? \"'

# return a substring of given string with a start and end 
def subString(reply, start, end):
    sub = reply [start: end:1]
    return sub

# takes a string seperated by commas and turns it into an array
def songarray (reply):
    songs = str.split(reply)
    return songs


q = Queue()
# takes in the text and turns it into speech
def speechbot ():
    #try:
        #os.remove('api/static/audio.wav')
    #except:
        #print("audio file not found.")
    audio = generate(
        text = q.get(),
        voice = Voices.from_api() [1],
        
    )
    save (audio, 'static/audio.wav')
    


messages = []
messages.append({"role": "system", "content": instructions})


response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages)
reply = response["choices"][0]["message"]["content"]
messages.append({"role": "assistant", "content": reply})

q.put(reply)
speechbot()

def queue(songs):
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect(url_for("login", _external = False))
    sp = spotipy.Spotify(auth=token_info['access_token']) 
    for x in songs:
        song_id=(sp.search(x, limit=1, type='track', market='ES') ['tracks']['items'][0]['uri'])
        sp.add_to_queue(song_id, device_id=None)
    speechbot()
    return redirect(url_for('host', _external = True))





@app.route ('/hostfirst', methods = ['GET', 'POST'])
def hostfirst():
    if request.method == 'POST':
        text = request.form['text']
        processed_text = text.upper()
        message = processed_text
        messages.append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages)
        reply = response["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": reply})

        # get substring of message before array of songs and print
        try:
            before = subString(reply, 0 ,reply.index('[') )
            q.put(before)
            songs = subString(reply,(reply.index('[')+1), reply.index(']') )
            # Turn songs into array of strings
            songs_array = songarray(songs)
            queue(songs_array)
            stor = subString(reply, (reply.index(']')+1),(len(reply)+1))
            q.put(stor)
            return redirect(url_for('host', _external = True))
        except:
            return render_template('hostfirst.html')
                
    else:
        audio_filename = 'audio.wav'
        response = make_response(render_template("hostfirst.html", audio_src=url_for('static', filename=audio_filename)))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    

@app.route('/host')
def host():
    audio_filename = 'static/audio.wav'

    # Read the binary contents of the .wav file
    with open(audio_filename, 'rb') as audio_file:
        audio_data = audio_file.read()

    # Encode the audio data to base64
    audio_base64 = base64.b64encode(audio_data).decode()

    return render_template("host.html", audio_base64=audio_base64)



@app.route('/login')
def login():
    sp_oath = create_oath()
    auth_url = sp_oath.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oath = create_oath()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oath.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('home', _external = True))


@app.route('/play')
def play():
    speechbot()
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect(url_for("login", _external = False))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    sp.next_track(device_id=None)
    return redirect(url_for('hostfirst', _external = True))

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        sp_oath = create_oath()
        token_info = sp_oath.refresh_access_token(token_info['refresh_token'])
    return token_info



def create_oath():
    return SpotifyOAuth(
        client_id="be010e2ac3534c1298858b58f2cf2fcd",
        client_secret= os.environ['SP_CLIENT_SECRET'],
        redirect_uri=url_for('redirectPage', _external = True),
        scope="user-modify-playback-state"
    )

app.run()