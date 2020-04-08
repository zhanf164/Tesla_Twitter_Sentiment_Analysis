# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 23:02:00 2019

@author: zach
"""

#the way ive written this looks like a jupyter notebook, perhaps I should convert it over to one. 

import tweepy as tw
from datetime import datetime
from collections import Counter
import re
import string
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

consumer_key = '9p6xgA8g2tS5QBfoaQTaS3wSv'
consumer_secret = 'qoNO6ecD8JituaFgnSYaamjOa6otBPaYeCaqh476BQSrhVedni'
access_token = '742072568367054853-SEbq8RRa0f089HTXhpb0iQjMipQ9FTV'
access_secret = '4ndzPfaWvp8L7tDMNuZ0lXzfWQdkcR4RaXw9Y5lwEktdh'

auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tw.API(auth, wait_on_rate_limit=True)


#Gather tweets for $TSLA up to 10,000 of them. I dont know how many there will be in total for each day so I will check that later
tweets = []
for tweet in tw.Cursor(api.search, q="$TSLA", Since="2020-01-01", lang="en").items(100000):
    tweets.append(tweet)
len(tweets)
#Unfortunately, I didnt get as many tweets as I requested, I wonder why. 

#See how many tweets were made on each day
test = [tweet.created_at.strftime("%m/%d/%Y") for tweet in tweets]
c= Counter(test)
print(c)

#Looking at this, it appears that the tweets only occur within the last week. Looking further into Twitter API, it appears
#you can only retreive tweets that have been posted within the last 7 days. That's a bummer. 
#Remove any tweets that is flagged as a retweet and check the length of leftovers
non_RT = []
for tweet in tweets:
    if not tweet.retweeted:
        non_RT.append(tweet)
        
len(non_RT)

#From these non retweeted stocks, lets look at whether or not the tweet was about tsla only, not about tsla at all, or about tsla and other companies
tweets_about_TSLA_only = []
tweets_about_Multiple_stocks = []
tweets_about_other_stocks = []
for tweet in non_RT:
    matches = re.findall("\$[a-zA-Z]+", tweet.text)
    if len(matches) == 0:
        pass
    elif len(matches) == 1 and matches[0].upper() == '$TSLA': 
        tweets_about_TSLA_only.append(tweet)
    elif len(matches) == 1 and matches[0].upper() != '$TSLA':
        tweets_about_other_stocks.append(tweet)
    else:
        tweets_about_Multiple_stocks.append(tweet)
        
print(len(tweets_about_TSLA_only))
print(len(tweets_about_Multiple_stocks))
print(len(tweets_about_other_stocks))

#interestingly, it looks like we can get around 10,000 tweets that are just about tsla, now I feel like its possible that 
#these tweets could be links to articles or things like that, so I am going to look into them a little further to see 
#what is going on

for tweet in tweets_about_TSLA_only:
    print(tweet.text)
    
#I still see alot of retweets in here, so lets take a look at those using some simple regex since they all follow the pattern "RT @user:"
for tweet in tweets_about_TSLA_only:
   match = re.match('RT\s+\@[A-Za-z]+\:', tweet.text)
   if match:
       print(tweet.text + '\n------------------------------------------------\n')
       
#Some of these look unique and others dont, I suppose what I will do is trim the retweet portion if it exists, and 
#then create a new list of tweets that contain unique tweets by comparing them to tweets Ive already seen. 

not_seen_before = []
unique_tweets_about_TSLA_only = []
for tweet in tweets_about_TSLA_only:
    match =  re.match('RT\s+\@[A-Za-z]+\:', tweet.text)
    if match:
        new_text = ':'.join(tweet.text.split(':')[1:]) # This assumes that anything before the first ':' is just the RT symbol, and then rejoins the strings if there are any other colons in the text. 
        if new_text not in not_seen_before:
            not_seen_before.append(tweet.text)
            unique_tweets_about_TSLA_only.append(tweet)
        else:
            pass
    else:
        if tweet.text not in not_seen_before:
            not_seen_before.append(tweet.text)
            unique_tweets_about_TSLA_only.append(tweet)
        else:
            pass
print(len(unique_tweets_about_TSLA_only))
            

#Alright, so all ~8,000 of those tweets are looking unique to me. They still contain extraneous info that I will look to cut down now. 
#it makes sense to me to maybe move onto the sentiment analysis portion at this point. I may have to come back and filter later, but we will see
#Up to this point, I havent actually been trimming the tweets, just moving on with the whole tweet object, so I think I will have to do that now. 
#Ive been moving the whole object because it contains important other information besides just the tweet (like datetime), so my solution to trimming the tweet is to 
#set an attribute for each tweet object that contains the trimmed tweet. This will keep all relevant information for the tweet and allow me to easily access
#the full text as well as the trimmed text. 

for tweet in unique_tweets_about_TSLA_only:
    placehold_text = tweet.text.lower()
    placehold_text = re.sub('RT\s+\@[a-z1-9]+\:', '', placehold_text) # remove RT at start of tweets
    placehold_text = re.sub('\@[a-z1-9]+', '', placehold_text) # remove @ any users
    placehold_text = re.sub('https.+', '', placehold_text) # remove the links at the end of tweets
    placehold_text = re.sub('rt\s+\:', '', placehold_text) 
    placehold_text = re.sub('rt\s+[a-z1-9]+\s+\:', '', placehold_text)
    placehold_text = re.sub('\s[1-9]+\s', '', placehold_text) # get rid of just numbers
    placehold_text = re.sub('\w*\d\w*', '', placehold_text) #get rid of words that contain numbers inside of them or numbers with letters on either side
    placehold_text = re.sub('rt.+\:', '', placehold_text)
    placehold_text = re.sub('\n', '', placehold_text) # remove new lines
    placehold_text = re.sub('\"', '', placehold_text)
    almost_final = placehold_text.translate(str.maketrans("","",string.punctuation)) #lets remove all punctuations
    final = almost_final.encode('ascii', 'ignore').decode('ascii') # There are also some emojis laying around, luckily I found this one liner on SO to axe them
    setattr(tweet, 'trimmed_text', final) # finally lets set this as an attributte to the actual tweet object itself. Not sure if this is the best idea, since it will change earlier instances, but oh well. 

#id like to look at the date distribution for these final tweets again
dates = [tweet.created_at.strftime("%m/%d/%Y") for tweet in unique_tweets_about_TSLA_only]
c = Counter(dates)
print(c)

#Still getting a few hundred tweets per day. Not too shabby, more than I would expect
#After about 95 steps, it looks like we finally have tweets that are just plain text about tesla, so now may be the time to build our dataframe
#I need to find something unique to index the entries by, my first guess is tweet id, so lets look at that

ids = [tweet.id for tweet in unique_tweets_about_TSLA_only]
len(ids)
len(set(ids))

#looks like id will work, so lets write some info to an outfile that we can then turn into a dataframe later. i could have just manually entered them into the dataframe, but I want that file for debugging in the future. 

tweet_dict = {}
for tweet in unique_tweets_about_TSLA_only:
    tweet_dict[str(tweet.id)] = [tweet.created_at.strftime("%m/%d/%Y"), tweet.user.screen_name, tweet.trimmed_text.strip()]
    
with open('C:/Users/zach/Desktop/Scripts/unique_TSLA_tweet_data.csv', 'w') as f:
    f.write("Tweet_id,date,user,text\n")
    for key, value in tweet_dict.items():
        f.write(key + ',' + ','.join(value) + '\n')
 
 

#time to run count vectorization in order to get word occurences, now things are starting to get fun

texts = [tweet.trimmed_text.strip() for tweet in unique_tweets_about_TSLA_only] # create a list with just the texts in them. 

vectorizer = CountVectorizer(stop_words = 'english') # create a vectorizer instance taking into account english stop words
matrix = vectorizer.fit_transform(texts)

print(vectorizer.get_feature_names()) # This shows which words were used for counts, it appears this actually worked pretty well!
df = pd.DataFrame(matrix.toarray(), columns=vectorizer.get_feature_names()) # our dataframe is looking pretty big, but just what I would expect at this point
df2 = pd.read_csv('C:/Users/zach/Desktop/Scripts/Twitter_TSLA_Anlaysis/unique_TSLA_tweet_data.csv')# This is a dataframe of the csv containing tweet date, user, and id

#Time to explore this data and see what people seem to be saying about TSLA and see if we can glean any information
#I'll start using text blob in order to look at the sentiment of each tweet


df2["test"] = df2["text"].map(lambda x: TextBlob(str(x))) # create column with textblob
df2["sent"] = df2["test"].map(lambda x: x.sentiment) #create column with the sentiment analysis
df2["polarity"] = df2["test"].map(lambda x: x.sentiment.polarity) # append a final column that contains the polarity value for each tweet

time = pd.Series(data=df2["polarity"].values, index=df2["date"]) # create a time series to look at polarity per date
time.groupby(['date']).describe() # group them by date, and then look at average polarity

dates = list(time.groupby(['date']).describe().index)#extract the dates to plot
means = list(time.groupby(['date']).describe()["mean"]) # extract the means to plot
plt.plot(dates, means)
plt.xticks(rotation=90) #rotate dates on the axis so they are readable
plt.show()

#Too bad the twitter API only allows you to access tweets from the last 7 days, or else we could have looked deeper into the past 
