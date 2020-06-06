# Tweet creator with ML
This is a script that uses markov-chains to parse tweets written by any user and create tweets using what they say.

## Usage
You need to create a .json file called secret.json storing there as variables the API_key, API_secret_key, Access_token and Access_token_secret that you can obtain from the [Twitter API](https://developer.twitter.com/en/docs)

## Libraries used
1. [Tweepy](https://github.com/tweepy/tweepy): to ease the GET requests to the Twitter API
2. [Nltk](https://www.nltk.org/): to ease the tokenization of the tweets