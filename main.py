import os
import json
import tweepy
import math
import time
import argparse
from nltk.tokenize import word_tokenize
from collections import Counter
import random
from pathlib import Path


class Main:

    def __init__(self):

        if Path('secret.json').exists():
            with open('secret.json') as data_file:
                data = json.load(data_file)
        else:
            raise Exception("Neeed to create a secret.json file with your API keys")
        consumer_key = data['API_key']  # Add your API key here
        consumer_secret = data['API_secret_key']  # Add your API secret key here
        access_token = data['Access_token']
        secret_access_token = data["Access_token_secret"]
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, secret_access_token)

    def main(self):
        parser = argparse.ArgumentParser(description='Analize tweets of a user to make a markov chain of it')
        users_group = parser.add_mutually_exclusive_group(required=True)
        users_group.add_argument('-u', '--username', type=str, help="username you want to work with")
        users_group.add_argument('-U', '--usernames', type=str, help="usernames separated by commas")
        parser.add_argument('-R', '--retrieve', dest='retr', action='store_true', default=False, help='retrieve some of the user tweets and store them in a json file')
        parser.add_argument('-M', '--markov', dest='mark', action='store_true', default=False, help='do the markov chain with the data stored of that user.')

        args = parser.parse_args()

        usernames = []
        if args.username:
            usernames.append(args.username)
            print("The username: " + usernames[0])
        elif args.usernames:
            usernames_str = args.usernames
            usernames = usernames_str.split(",")
            for user in usernames:
                user = user.strip()
                print("The username: " + user + " was added")

        if args.mark:
            # TODO: rename the results.json to tokens.json or tokens.bin
            if Path('result.json').exists():
                # FIXME: only working for a single user
                self.tokenize_tweets(usernames[0])
            else:
                raise Exception("There is no retrieved data for that user, you may run this command with the argument --retrieve")

        elif args.retr:
            # FIXME: only working for a single user
            self.retrieve_tweets(usernames[0])

        else:
            # Do the entire process
            for user in usernames:
                self.retrieve_tweets(user)

            self.tokenize_tweets(usernames[0])

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
        # FIXME: the "." handling is off
        for tweet_tokenized in tweets_tokenized:
            for i, token in enumerate(tweet_tokenized):
                # BIGRAMS
                if token not in bigrams:
                    bigrams[token] = []
                if i+1 < len(tweet_tokenized):
                    bigrams[token].append(tweet_tokenized[i+1])
                else:
                    bigrams[token].append(".")  # FIXME: the "." handling is off

                # TRIGRAMS
                if i+1 < len(tweet_tokenized):
                    token = str(token) + " " + tweet_tokenized[i+1]
                    if token not in trigrams:
                        trigrams[token] = []
                    if i+2 < len(tweet_tokenized):
                        trigrams[token].append(tweet_tokenized[i+2])
                    else:
                        trigrams[token].append(".")  # FIXME: the "." handling is off

        for token in bigrams:
            aux = Counter(bigrams[token])
            num = len(bigrams[token])
            for k in aux:
                aux[k] = aux[k]/num
            bigrams[token] = aux

        for token in trigrams:
            aux = Counter(trigrams[token])
            num = len(trigrams[token])
            for k in aux:
                aux[k] = aux[k]/num
            trigrams[token] = aux

        with open('trigrams.json', 'w') as fp:
            json.dump(trigrams, fp)

        self.create_random_tweet(bigrams, trigrams=trigrams)

    def create_random_tweet(self, bigrams, trigrams={}):
        max_len_tweet = 140

        # 'cute': Counter({'pero': 0.25, 'please': 0.25, 'to': 0.25, '.': 0.25})
        tweet_tokens = [0]

        # First word selected on bigrams
        token = "0"
        while token == "0":
            for word in bigrams[0]:
                prob = 0
                rand = random.uniform(0, 1)
                if(bigrams[0][word] + prob > rand):
                    tweet_tokens.append(word)
                    break
                else:
                    prob += bigrams[0][word]

            tweet_tokens[0] = "0"
            token = " ".join(tweet_tokens[-2:])
        while tweet_tokens[-1] != '.' and len(" ".join(tweet_tokens[1:])) < max_len_tweet:
            token = " ".join(tweet_tokens[-2:])

            for word in trigrams[token]:
                if(trigrams[token][word] + prob > rand):
                    tweet_tokens.append(word)
                    break
                else:
                    prob += trigrams[token][word]

        print("=======================================\n Generated tweet: \n")
        print(" ".join(tweet_tokens[1: -1])+".")

    def retrieve_tweets(self, username):
        print("Retrieving", username, "timeline")

        # Get the acutal list of retrieved tweets
        tweets = []

        if Path('result.json').exists():
            with open('result.json') as f:
                tweets = json.load(f)

        # Getting the API
        api = tweepy.API(self.auth)

        count = 300
        tweets_count = 0
        non_rt_count = 0
        last_tweet_count = 0
        repeats = 0
        while count > 1 and tweets_count < 3200 and repeats < 3:
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
                        # print("Tweet #" + str(tweets_count) + ": ")
                        # print(tweet.full_text[0:40]+"...")
                        tweets_count += 1
                        non_rt_count += 1

            with open('result.json', 'w') as fp:
                json.dump(tweets, fp)

            count -= 1
            print("Time left to retrieve: " + str(count * 3) + "s")
            print("Total tweets analized: " + str(tweets_count) + "\t\t non RT: "+str(non_rt_count))

            if last_tweet_count == non_rt_count:
                repeats += 1

            last_tweet_count = non_rt_count

            time.sleep(1.1)  # You can lower it to 1 but it's too adjusted to the API limits


if __name__ == "__main__":
    Main().main()
