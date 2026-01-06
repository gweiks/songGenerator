1. Project Purpose / Motivation
This project was created to explore natural language generation using Markov chain models and to compare unigram and bigram lyric generation.

2. Usage
Select a training model (unigram or bigram), then generate lyrics using the trained model.

3. How It Works (High Level)
The application scrapes song lyrics, cleans and tokenizes the text, trains a Markov chain model, and generates new lyrics based on probabilistic word transitions.

4. How It Works (In Depth)
The program scrapes Maroon 5 lyrics from www.streetdirectory.com and analyzes them to produce new, similar lyrics.

There are two available model training methods:

- Unigram Model
The unigram model maps each word from Maroon 5 songs to the words that most commonly follow it. Words that appear more frequently after a given word are more likely to be generated.

- Bigram Model
The bigram model uses pairs of words as keys instead of single words. This makes the output more coherent and realistic, but less creative. As a result, the lyrics may regurgitate original songs.

Note: Maroon 5 lyrics have all been prescraped but you are welcome to rescrape them if you wish. It may take 10 minutes to scrape.

5. Limitations
- Generated lyrics may closely resemble original songs, especially when using the bigram model.
- Markov models do not understand semantic meaning or grammar.