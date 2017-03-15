# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 17:27:23 2017

@author: Timo van Niedek
"""

import spotipy
import spacy
import codecs
import random
import json 
import requests
import time
import urllib
import configparser as cp

"""
    Load the configuration file (bot.ini)
    bot.ini requires at least the following two lines

[BotConfig]
TOKEN = <token>

    with quotes.
"""
config = cp.ConfigParser()
config.read('bot.ini')

TOKEN = config.get('BotConfig','TOKEN')
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

"""
    Define the canned responses
"""
GREETINGS = ['hi','hello','yo','sup','howdy','hey','hiya']
GREETING_RESPONSES = ["Hey there!","Hello!","Hiya!"]
GREETING_WITH_NAME = ["Hey {}", "Hi {}!", "Hello again, {}", "Welcome back, {}"]
ARTISTS_QUESTION = ["What artists or bands do you like?",
                    "Can you tell me some artists that you like?",
                    "Which artists do you listen to?"]
RESPONSE_TO_ARTISTS = ["Okay, I'm going to look for artists similar to ",
                       "I might know something kinda like ",
                       "Let me see, I might know "]
RESPONSE_TO_UNKNOWN_QUESTION = ["I don't know that, but I can help you find some artists if you tell me what you listen to!",
                               "I'm not sure.. I only know about musicians and bands. Tell me, which artists do you like?",
                               "My knowledge is limited to music only.. maybe you could tell me what kind of artists you like?"]
RESPONSE_TO_UNKNOWN_STATEMENT = ["Okay, great!", "Cool 😊"]
YML = [", you might also like:\n",", I can recommend:\n"]
IYL = ["If you like ", "Since you listen to ", "Similar to "]

KNOWN_NAMES = []

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def send_message(text, chat_id):
    """
    Send a message to a given chat.
    """
    print("Sending message: "+text)
    text = urllib.parse.quote_plus(text) # (python3)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)

def make_and_list(strings):
    """ 
    Helper function for creating a string list like:
        "apples, pears, and kiwis"
    """
    response = ""
    for i in range(0, len(strings)):
        if (i == len(strings)-2):
            if (len(strings) > 2):
                response = response + strings[i] + ", and "
            else:
                response = response + strings[i] + " and "
        elif (i == len(strings) - 1):
            response = response + strings[i]
        else:
            response = response + strings[i] + ", "
    return response

def make_or_list(strings):
    """ 
    Helper function for creating a string list like:
        "apples, pears, or kiwis"
    """
    response = ""
    for i in range(0, len(strings)):
        if (i == len(strings)-2):
            if (len(strings) > 2):
                response = response + strings[i] + ", or "
            else:
                response = response + strings[i] + " or "
        elif (i == len(strings) - 1):
            response = response + strings[i]
        else:
            response = response + strings[i] + ", "
    return response

def extract_pos(doc, verbose=False):
    """
    Extract the Parts of Speech of a doc
    """
    verbs = []
    nouns = []
    pronouns = []
    adjectives = []
    adverbs = []
    noun_chunks = []
    words = []
    for word in doc:
        words.append(word.lower_)
        if (verbose):
            print(word, word.pos_)
        pos = word.pos_
        if (pos == 'VERB'):
            verbs.append(word.lower_)
        elif (pos == 'NOUN' or pos == 'PROPN'):
            nouns.append(word.lower_)
        elif (pos == 'PRON'):
            pronouns.append(word.lower_)
        elif (pos == 'ADJ'):
            adjectives.append(word.lower_)
        elif (pos == 'ADV'):
            adverbs.append(word.lower_)
    for noun_chunk in doc.noun_chunks:
        noun_chunks.append(noun_chunk.text)
    return verbs, nouns, pronouns, adjectives, adverbs, noun_chunks, words
    
class ResponseGenerator:
    """A class for generating responses based on inputs."""
    def __init__(self, artist_file):
        print("RG: loading English vocabulary")
        self.nlp = spacy.load('en')
        print("RG: creating Matcher")
        self.matcher = spacy.matcher.Matcher(self.nlp.vocab)
        print("RG: adding artists to matcher")
        self.add_artists_to_matcher(artist_file, self.matcher)
        print("RG: ready")
        self.name_for_id = {}
        
    def generate_response(self, updates, sp):
        """
        Generate responses for all updates recieved from Telegram.
        """
        for update in updates["result"]:
            # Check if we know this person
            chatter_id = update["message"]["from"]["id"]
            first_name = update["message"]["from"]["first_name"]
            chat = update["message"]["chat"]["id"]
            print(update)
            text = update["message"]["text"]
            doc = self.nlp(text)
            self.matcher(doc)
            is_greeting = self.text_contains_greeting(doc)
            artists = self.text_contains_artist(doc)
            if (is_greeting):
                if (chatter_id in self.name_for_id):
                    response = random.choice(GREETING_WITH_NAME).format(first_name)
                    send_message(response, chat)
                    response = random.choice(ARTISTS_QUESTION)
                    send_message(response, chat)
                else:
                    response = random.choice(GREETING_RESPONSES)
                    send_message(response, chat)
                    send_message("I am MusicBot 1.0. I can recommend some artist if you tell me what you like.")
                    response = random.choice(ARTISTS_QUESTION)
                    send_message(response, chat)
            elif (artists):
                response = random.choice(RESPONSE_TO_ARTISTS) + make_or_list(artists) + "..."
                send_message(response,chat)
                response = self.recommend_artists(artists, sp)
                send_message(response,chat)
            elif (self.text_contains_question(doc)):
                send_message(self.respond_to_question(doc),chat)
            else:
                response = self.respond_to_statement(doc)
                send_message(response, chat)
            self.name_for_id[chatter_id] = first_name

    def text_contains_greeting(self, doc):
        """
        Check if a text contains a greeting.
        """
        for word in doc:
            if(word.lower_ in GREETINGS):
                return True
        return False
    
    def text_contains_artist(self, doc):
        """
        Check if a text contains an Artist based on the artists data file.
        """
        artists = []
        for ent in doc.ents:
            if(ent.label_ == 'ARTIST'):
                print("Recognized {}".format(ent.text))
                artists.append(ent.text)
        return artists

    def text_contains_question(self, doc):
        """
        Check if a text contains a question mark.
        """
        for word in doc:
            if (word.text == "?"):
                return True
        return False
    
    def respond_to_statement(self, doc):
        """
        Return a response to a statement (defined as not containing a question mark).
        The bot will respond to "You are ..." with "No, you are ...!" or otherwise
        state that it does not understand.
        """
        verbs, nouns, pronouns, adjectives, adverbs, noun_chunks, words = extract_pos(doc)
        if ('you' in pronouns):
            # Statement is referring to the bot
            if ('are' in verbs):
                # Reply with 'no u' kinda reply
                np_candidate = None
                for noun_chunk in noun_chunks:
                    if (not(noun_chunk.lower() in ['you','i'])):
                        np_candidate = noun_chunk
                        break
                if (not np_candidate):
                    # Just pick the first adverb or adjective
                    if (len(adverbs) > 0):
                        np_candidate = adverbs[0]
                    elif (len(adjectives) > 0):
                        np_candidate = adjectives[0]
                    else:
                        return random.choice(RESPONSE_TO_UNKNOWN_STATEMENT)
                return "No, you are {}!".format(np_candidate)
            else:
                return random.choice(RESPONSE_TO_UNKNOWN_STATEMENT)
        else:
            return random.choice(RESPONSE_TO_UNKNOWN_STATEMENT)
            
    def respond_to_question(self, doc):
        """
        Generate a semi-canned response to any question a chatter might have.
        Most of the time, the bot will respond by stating that it does not know
        the answer to the question.
        """
        verbs, nouns, pronouns, adjectives, adverbs, noun_chunks, words = extract_pos(doc)
        if ('you' in pronouns):
            # Question is referring to the bot
            if (any(v in verbs for v in ['can','could','would'])):
                # Can you ... ?
                if (any(n in words for n in ['music','musician','musicians','band','artist','artists','bands'])):
                    # Can you ... <something related to music>?
                    if (any(v in verbs for v in ['recommend','suggest'])):
                        return "Yes, I can recommend some artists! " + random.choice(ARTISTS_QUESTION)
                    else:
                        # Can you ... <something related to music but not recommending>
                        return "No, but I can recommend some music for you. " + random.choice(ARTISTS_QUESTION)
                else:
                    return "Unfortunately not. I can only recommend music. " + random.choice(ARTISTS_QUESTION)
            elif ('are' in verbs):
                if (any(n in nouns for n in ['who','what'])):
                    # Question is asking who or what the bot is
                    return "I am MusicBot 1.0. I can help you with recommending artists. " + random.choice(ARTISTS_QUESTION)
                elif ('how' in adverbs):
                    # Question is asking how the bot is doing
                    return "I am doing great, how are you? 😊 " + random.choice(ARTISTS_QUESTION)
                else:
                    return random.choice(RESPONSE_TO_UNKNOWN_QUESTION)
            elif (any(v in verbs for v in ['know','recognize','recognise','think'])):
                # Question about some knowledge
                if (any(n in words for n in ['music','musician','musicians','band','artist','artists','bands'])):
                    return "I can recommend some artists! " + random.choice(ARTISTS_QUESTION)
                else:
                    np_candidate = None
                    for noun_chunk in noun_chunks:
                        if (not(noun_chunk.lower() in ['what','who','you','anything','something','anybody','somebody'])):
                            np_candidate = noun_chunk
                            break
                    if (not np_candidate):
                        np_candidate = 'that'
                    return "I don't know {}. My knowledge is limited to musicians and bands only.. 🙁".format(np_candidate)
            else:
                # If we don't recognize any questions here, return a generic don't-know response
                return random.choice(RESPONSE_TO_UNKNOWN_QUESTION)
        else:
            # If we don't recognize any questions here, return a generic don't-know response
            return random.choice(RESPONSE_TO_UNKNOWN_QUESTION)
    
    def get_artist(self, name, sp):
        """
        Get the artist that best matches the name string in a Spotify query.
        """
        results = sp.search(q='artist:' + name, type='artist')
        items = results['artists']['items']
        if len(items) > 0:
            return items[0]
        else:
            return None
        
    def recommend_artists(self, input_artist_names, sp):
        """
        Find artists similar to the artists in input_artist_names.
        These artists are sorted least popular first to promote serendipity.
        Returns a string containing the response string for recommending artists.
        """
        related = []
        for name in input_artist_names:
            artist = self.get_artist(name, sp)
            if (artist):
                artist_id = artist['id']
                related_artists = sp.artist_related_artists(artist_id)['artists'][0:10]
                if (len(related_artists) > 0):
                    for artist in related_artists:
                        info = (artist['name'], artist['popularity'])
                        print(info)
                        related.append(info)
                        print(related)
        if (len(related) == 0):
            if (len(input_artist_names) == 1):
                return "I don't know the artist " + input_artist_names[0] + " 🙁 It's probably too underground..",
            else:
                return "I don't know " + make_or_list(input_artist_names) + ". You must have a really unique taste in music."
        sorted_artists = sorted(related, key=lambda tup: tup[1])
        response = random.choice(IYL) + make_and_list(input_artist_names) + random.choice(YML)
        for i in range(0, 10):
            response = response + " - " + sorted_artists[i][0] + "\n"
        return response
    
    def add_artists_to_matcher(self, file, matcher):
        """
        Add the artists from a given file to the spaCy matcher.
        """
        with codecs.open(file, "r", encoding='utf-8') as f:
            entity_key = 1
            for line in f:
                artist_full = line.rstrip()
                artist_parts = artist_full.split(' ')
                specs = []
                for w in artist_parts:
                    specs.append({spacy.attrs.ORTH: w})
                self.matcher.add(entity_key=entity_key,label='ARTIST',attrs={},specs=[specs], on_match=self.merge_phrases)
                entity_key += 1
    
    def merge_phrases(self, matcher, doc, i, matches):
        '''
        Merge a phrase. We have to be careful here because we'll change the token indices.
        To avoid problems, merge all the phrases once we're called on the last match.
        '''
        if i != len(matches)-1:
            return None
        spans = [(ent_id, label, doc[start : end]) for ent_id, label, start, end in matches]
        for ent_id, label, span in spans:
            span.merge('NNP' if label else span.root.tag_, span.text, self.nlp.vocab.strings[label])

def main():
    response_generator = ResponseGenerator('artists.txt')
    
    sp = spotipy.Spotify()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            response_generator.generate_response(updates,sp)
        time.sleep(0.5)


if __name__ == '__main__':
    main()