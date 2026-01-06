from multiprocessing import process
from flask import Flask, send_file, jsonify, request
import os
import time
from numpy.ma.core import true_divide
from pandas.core.config_init import data_manager_doc
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import random
import json

app = Flask(__name__)

# Store chain globally
chain = None
unigram = True

@app.route('/')
def home():
    return send_file('home.html')

@app.route("/api/save", methods=['POST'])
def save():
    global unigram

    data = request.get_json(silent=True) or {}
    value = data.get("value", True)

    if isinstance(value, bool):
        unigram = value
    else:
        unigram = bool(value)

    return jsonify({'success': True, 'unigram': unigram})

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
        chain = train_model(df, unigram)
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
        song = generate_song(chain, unigram)
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


def preprocess_lyrics(lyrics):
    all_lyrics = []
    for lyric in lyrics:
        text = lyric.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        lines = text.split('\n')

        lines[0] = "<START> " + lines[0]
        lines[-1] = lines[-1] + " <END>"
        all_lyrics.append(lines)
    return all_lyrics


def train_model(df, unigram):
    """
    Trains the model on the lyrics.
    Args:
        df: pandas dataframe with the lyrics
    Returns:
        chain: dictionary of the words and the words that follow them
    """
    lyrics = df["Lyrics"].tolist()
    print(len(lyrics))
    processed_lyrics = preprocess_lyrics(lyrics)
    nGram = 1 if unigram else 2

    #create a dictionary of the words and the words that follow them
    chain = {"<START>":[]}

    for lyrics in processed_lyrics:
        words_in_song = []

        for i in range(len(lyrics)):
            words = (lyrics[i]).split()

            if i == 0:
                chain["<START>"].append(words[1])

            if i > 0:
                words.insert(0, "<N>")

            for word in words:
                words_in_song.append(word)

        for j in range(len(words_in_song) - nGram):
            key = words_in_song[j]
            if nGram == 2:
                key += (" " + words_in_song[j + 1])
            if key not in chain:
                chain[key] = []
            chain[key].append(words_in_song[j + nGram])

    return chain


def generate_song(chain, unigram = True):
    """
    Args:
        - chain: a dict representing a unigram Markov chain

    Returns:
        A string representing the randomly generated song.
    """
    #Initialize the words list with the tuple (randomly chosen from the start token)
    words = [random.choice(chain["<START>"])] 
    current_tuple = words[0] if unigram else "<START> " + words[0]

    #until we reach the end, continue down the markov chain finding the next word
    while ("<END>" not in current_tuple):
        next_word = random.choice(chain[current_tuple])
        words.append(next_word)
        current_tuple = (next_word) if unigram else (current_tuple.split(" ", 1)[0] + " " + next_word)

    # join the words together into a string with line breaks
    lyrics = " ".join(words[:-1])
    return "\n".join(lyrics.split("<N>"))

if __name__ == '__main__':
    app.run(debug=True, port=5000)