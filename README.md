# MusicBot
A Telegram chatbot for recommending music based on Spotify using spaCy created by Timo van Niedek.

----

# Introduction

MusicBot uses the Telegram bot API to create an interactive interface for requesting artist names that are similar to artists that the user tells MusicBot. It can also respond to some basic questions and statements.

# Dependencies

The bot requires Python version 3.3 or higher. The required packages are:

* [spaCy](https://spacy.io/) for parsing the text
* [spotipy](https://github.com/plamere/spotipy) for retrieving similar artists
* [requests](https://github.com/kennethreitz/requests)

If you want to run this code yourself, don't forget to add `bot.ini` file containing at least the follwing lines:

	[BotConfig]
	TOKEN = <your telegram token>

without the <>.

# Example conversations

A simple example showing the main functionality of MusicBot is shown below.

	User: 		Hello MusicBot!
	MusicBot: 	Hey there!
	MusicBot:	I am MusicBot 1.0. I can recommend some artist if you tell me 
				what you like.
	MusicBot:	Which artists do you listen to?
	User:		I usually listen to artists like The Beatles and The Doors, 
				but somtimes I like to listen to some lesser known artists 
				such as Mura Masa, Tennyson and The M Machine.
	MusicBot:	Let me see, I might know The Beatles, The Doors, Mura Masa, 
				Tennyson, or The M Machine...
	MusicBot:	Similar to The Beatles, The Doors, Mura Masa, Tennyson, 
				and The M Machine, you might also like:
 				 - Milo Mills
				 - Dog Blood
				 - Lindsay Lowend
				 - Pascäal
				 - GEOTHEORY
				 - Alvin Risk
				 - Jim Morrison
				 - The Yardbirds
				 - The Byrds
				 - The Hollies
	User:		Okay, thanks!
	MusicBot:	Cool :)

As can be seen,  the bot takes some recommendations for each artist and combines them into one list sorted from least popular to most.

# How it works

When MusicBot is started, it loads a list of known artists and adds them to the spaCy Matcher. The list of artists is included in this repository, and is downloaded from the [Last.fm](https://www.last.fm/) public API using the [pylast](https://github.com/pylast/pylast) package (not included in the dependency list since the artists are pre-downloaded). The list includes the top 10000 artists retrieved at March, 2017. Note that this step takes a while, since the English model and artist list have to be loaded.

When a message is recieved by MusicBot, it is first checked for greetings using a predefined list of greeting words. If so, a greeting is sent to the user, which will contain the user's name if they have spoken to MusicBot before (given that the bot did not restart after then). Then, it is scanned for artist names using the spaCy Matcher class. If this is not the case, a check is performed whether or not the message was a question, and if so, an appropriate response is formed from a predefined list. Otherwise, the message is treated as a statement, which will generate a different response.

When a user sends a message containing one or more known artists, the bot will query the Spotify API for each of those artists, compiling lists of relevant artists. These lists are sorted in increasing popularity, such that the *least* popular artist will appear first. This was an important criterium, since we want to show artists that the user is less likely to already know, and thus stimulate exploration of lesser known artists.

# Possible extensions

Since creating MusicBot was a project for only a couple weeks, there are many possible extensions that were beyond the scope of this project:

* A memory all artists that the user has mentioned in the past. This can be used to further specify the recommendations.
* A smarter general response system. The current implementation fails in many cases to correctly respond to statements or questions beyond requests for recommendations.
* A recommendation system based on not only artists, but also genre, albums or specific songs.
* In the same vein, an album or song recommendation system besides just artists. 