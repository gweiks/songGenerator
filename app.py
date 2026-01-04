from flask import Flask, send_file, jsonify
import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import random
import json

app = Flask(__name__)

# Store chain globally
chain = None

@app.route('/')
def home():
    return send_file('home.html')

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    try:
        df = scrape_lyrics()
        return jsonify({'success': True, 'message': f'Scraped {len(df)} songs'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/train', methods=['POST'])
def api_train():
    global chain
    try:
        if not os.path.exists('maroon_5_lyrics.csv'):
            return jsonify({'success': False, 'error': 'Please scrape lyrics first'}), 400
        df = pd.read_csv('maroon_5_lyrics.csv')
        chain = train_model(df)
        with open('chain.json', 'w') as f:
            json.dump(chain, f)
        return jsonify({'success': True, 'message': 'Model trained successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    global chain
    try:
        if chain is None:
            if os.path.exists('chain.json'):
                with open('chain.json', 'r') as f:
                    chain = json.load(f)
            else:
                return jsonify({'success': False, 'error': 'Please train model first'}), 400
        song = generate_song(chain)
        return jsonify({'success': True, 'song': song})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def scrape_lyrics():
    """
    Scrapes the lyrics from the webpage and organizes them into a dataframe.
    Args:
        None
    Returns:
        df: pandas dataframe with the title and lyrics
    """

    songs = []
    url = "https://www.streetdirectory.com/lyricadvisor/artist/cclco/maroon_5/"

    #scrape the songs from the webpage
    for i in range(1,4):
        response = requests.get(url + str(i) + "/")
        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.find_all("a", class_="tahoma13purplebold"):
            href = a_tag.get("href")

            if href and "lyricadvisor/song" in href:
                songs.append(href)

        time.sleep(5)

    song_lyrics = []
    song_names = []

    #organize the lyric data into a dataframe (title and lyrics)
    for song in songs:
        response = requests.get(song)

        soup = BeautifulSoup(response.text, "html.parser")

        lyrics_div = soup.find("div", id="content_lyric_clean")

        if lyrics_div != None:
            lyrics = "\n".join(lyrics_div.stripped_strings).replace("\u2019", "")
            lyrics = lyrics.encode("latin1").decode("utf-8").replace("[CHORUS]", " ")
            song_lyrics.append(lyrics)

        song_name = soup.find("a", class_ = "tahoma33purple").text.replace(" Lyrics", "")
        song_names.append(song_name)
        print(f"Scraped {song_name}")
        time.sleep(3)

    df = pd.DataFrame({"Title": song_names, "Lyrics": song_lyrics})
    df.to_csv('maroon_5_lyrics.csv', index=False)

    return df


def train_model(df):
    """
    Trains the model on the lyrics.
    Args:
        df: pandas dataframe with the lyrics
    Returns:
        chain: dictionary of the words and the words that follow them
    """

    lyrics = df["Lyrics"].tolist()
    all_lyrics = []

    for lyric in lyrics:
        text = lyric.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        lines = text.split('\n')

        #add the start and end tokens to the lyrics so we know where to start and end the song
        lines[0] = "<START> " + lines[0]
        lines[-1] = lines[-1] + " <END>"

        all_lyrics.append(lines)
    
    #create a dictionary of the words and the words that follow them
    chain = {"<START>": []}

    for lines in all_lyrics:
        words_in_song = []

        for i in range(len(lines)):
            words = (lines[i]).split()

            if i > 0:
                words.insert(0, "<N>")

            for word in words:
                words_in_song.append(word)

        for j in range(len(words_in_song) - 1):
            #if the word is not in the dictionary, add it
            if words_in_song[j] not in chain:
                chain[words_in_song[j]] = []

            #add the word and the word that follows it to the dictionary
            chain[words_in_song[j]].append(words_in_song[j + 1])

    return chain


def generate_song(chain):
    """
    Args:
        - chain: a dict representing a unigram Markov chain

    Returns:
        A string representing the randomly generated song.
    """
    #Initialize the words list with the first word (randomly chosen from the start token)
    words = [random.choice(chain["<START>"])]

    #Generate the next word, appending to the words list
    current_word = words[0]

    #Generate the next word until the end token is reached
    while (current_word != "<END>"):
        next_word = random.choice(chain[current_word])
        words.append(next_word)
        current_word = next_word

    # join the words together into a string with line breaks
    lyrics = " ".join(words[:-1])
    return "\n".join(lyrics.split("<N>"))

if __name__ == '__main__':
    app.run(debug=True, port=5000)