import os
import json
import tweepy
import math
import time
import argparse
from nltk.tokenize import word_tokenize
from collections import Counter
import random


class Main:

    def __init__(self):
        with open('secret.json') as data_file:
            data = json.load(data_file)
        consumer_key = data['API_key']  # Add your API key here
        consumer_secret = data['API_secret_key']  # Add your API secret key here
        access_token = data['Access_token']
        secret_access_token = data["Access_token_secret"]
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, secret_access_token)

    def main(self):
        # parser = argparse.ArgumentParser(description='Analize tweets of a user to make a markov chain of it')
        # parser.add_argument('-R', '--retrieve', dest='retr', action='store_true', default=False, help='retrieve some of the user tweets.')
        # parser.add_argument('-M', '--markov', dest='mark', action='store_true', default=False, help='do the markov chain with the data stored of that user.')

        username = "realDonaldTrump"

        # self.retrieve_tweets(username)

        # TOKENIZATION
        self.tokenize_tweets(username)

    def tokenize_tweets(self, username):
        # Do we have a list of tweets of that user?
        tweets = []
        with open('result.json') as f:
            tweets = json.load(f)

        for tweet in tweets:
            if tweet['user'] != username:
                tweets.remove(tweet)

        if not tweets:
            print("There are no retrieved tweets for that user, try to retrieve them first")
            return 0

        tweets_text = []  # All the tweets text combined
        for tweet in tweets:
            tweets_text.append(tweet['text'])

        tweets_tokenized = []
        i = 0
        for i in range(len(tweets_text)):
            tweets_tokenized.append(word_tokenize(tweets_text[i]))
            tweets_tokenized[i].insert(0, 0)
            j = 0

            while j in range(len(tweets_tokenized[i])):
                # Url that we don't want to have in account
                if tweets_tokenized[i][j] == 'http' or tweets_tokenized[i][j] == 'https':
                    if j+2 < len(tweets_tokenized[i]):
                        del tweets_tokenized[i][j:j+3]

                # Tagging a user, the user will tag himself
                # FIXME: find a better solution since it will cause to have a big probability in the markov chain
                elif tweets_tokenized[i][j] == '@':
                    if j+1 < len(tweets_tokenized[i]):
                        del tweets_tokenized[i][j:j+2]

                j += 1

            i += 1

        bigrams = {}  # one word and the next one with the counter
        trigrams = {}
        for tweet_tokenized in tweets_tokenized:
            for i, token in enumerate(tweet_tokenized):
                if token not in bigrams:
                    bigrams[token] = []
                if i+1 < len(tweet_tokenized):
                    bigrams[token].append(tweet_tokenized[i+1])
                else:
                    bigrams[token].append(".")

        for token in bigrams:
            aux = Counter(bigrams[token])
            num = len(bigrams[token])
            for k in aux:
                aux[k] = aux[k]/num
            bigrams[token] = aux

        # with open('bigrams.json', 'w') as fp:
        #     json.dump(bigrams, fp)
        self.create_random_tweet(bigrams)

    def create_random_tweet(self, bigrams):
        # First word is 0
        # Last word is .
        tweet_tokens = [0]
        i = 0
        # 'cute': Counter({'pero': 0.25, 'please': 0.25, 'to': 0.25, '.': 0.25})
        while tweet_tokens[-1] != '.' and len(" ".join(tweet_tokens[1:])) < 140:
            token = tweet_tokens[-1]
            prob = 0
            rand = random.uniform(0, 1)
            for word in bigrams[token]:
                if(bigrams[token][word] + prob > rand):
                    tweet_tokens.append(word)
                    break
                else:
                    prob += bigrams[token][word]

        print(" ".join(tweet_tokens[1:-1])+".")

    def retrieve_tweets(self, username):
        print("Retrieving", username, "timeline")

        # Get the acutal list of retrieved tweets
        tweets = []
        with open('result.json') as f:
            tweets = json.load(f)

        # Getting the API
        api = tweepy.API(self.auth)

        count = 300
        tweets_count = 0
        while count > 1 and tweets_count < 4800:
            # Getting the last tweet of that username
            max_id = math.inf
            found = False
            for tweet in tweets:
                if tweet['user'] == username and tweet['id'] < max_id:
                    max_id = tweet['id']
                    found = True

            if found:
                user_timeline = api.user_timeline(username, count=200, tweet_mode="extended", max_id=max_id)
            else:
                user_timeline = api.user_timeline(username, count=200, tweet_mode="extended")

            for tweet in user_timeline:
                tweets_count += 1
                if not hasattr(tweet, "retweeted_status"):
                    t = {"id": tweet.id, "user": username, "text": tweet.full_text, "date": str(tweet.created_at)}
                    if t not in tweets:
                        tweets.append(t)
                        print("Tweet #" + str(tweets_count) + ": ")
                        print(tweet.full_text[0:40]+"...")
                        tweets_count += 1

            with open('result.json', 'w') as fp:
                json.dump(tweets, fp)

            count -= 1
            print("Time left to retrieve: " + str(count * 3) + "s")
            print("Total tweets analized: " + str(tweets_count))
            time.sleep(3)


# class Tweet:
#     def __init__(self, id, text, date):
#         self.id = id
#         self.text = text
#         self.date = date

#     def toJSON(self):
#         return json.dumps(self, default=lambda o: o.__dict__,
#                           sort_keys=True, indent=4)


if __name__ == "__main__":
    Main().main()
