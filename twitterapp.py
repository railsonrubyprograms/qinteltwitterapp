import twitter
import heapq

class Twitter(object):

    def __init__(self):
        self.api = twitter.Api(consumer_key='yxVBTLApDLIywH7cGoUFRrPcF',
                               consumer_secret='dEDaqjBTXnoyHqmpZ39tjtcVrA5Ji80MlDoxmin2P92xTYsa83',
                               access_token_key='246983085-byjQJXVoHOEzqZyeImtIThM9mSgHiyAG9wp68uKY',
                               access_token_secret='uCKt4KPLHSuKaiFSCJUnMVMMCGFDoyptGpdSCghaNqNWz')
        self.statuses = []
        self.userName = None
        self.user = None
        self.userFriends = 0
        self.userFollowers = 0
        commonWords = open("commonWords.txt", "r")
        self.commonWords = set()
        self.setCommonWords(commonWords)
        happyWords = open("happyWords.txt", "r")
        self.happyWords = set()
        self.setHappyWords(happyWords)
        negativeWords = open("negativeWords.txt", "r")
        self.negativeWords = set()
        self.setNegativeWords(negativeWords)
        self.userTimeOffset = 0
        self.userID = 0
        self.userScreenName = ""

    def setCommonWords(self, commonWords):
        for line in commonWords:
            self.commonWords.add(line.split()[1])

    def setHappyWords(self, happyWords):
        for line in happyWords:
            self.happyWords.add(line.strip())

    def setNegativeWords(self, negativeWords):
        for line in negativeWords:
            self.negativeWords.add(line.strip())

    def run(self):
        self.getUser()
        print "Gathering " + self.user.screen_name + "'s tweets...this might take a while..."
        self.getUserPosts()

    def getUser(self):
        if (self.userName == None): self.userName = raw_input("Input account identifier (user_id or screen_name): ")
        try:
            self.userName = int(self.userName)
        except:
            pass
        if (type(self.userName) == str):
            self.user = self.api.GetUser(screen_name=self.userName)
        elif (type(self.userName) == int):
            self.user = self.api.GetUser(user_id=self.userName)
        else: raise Exception("Not a valid user identifier")
        self.userFriends = self.user.friends_count
        self.userFollowers = self.user.followers_count
        self.userID = self.user.id
        self.userScreenName = self.user.screen_name
        if (self.user.utc_offset == None): self.userTimeOffset = 0
        else: self.userTimeOffset = self.user.utc_offset / 3600

    def getUserPosts(self):
        if (type(self.userName) == str):
            self.statuses.extend(self.api.GetUserTimeline(screen_name=self.userName))
            max_id = self.statuses[-1].id - 1
            while True:
                tempStatuses = self.api.GetUserTimeline(screen_name=self.userName, max_id=max_id)
                if (len(tempStatuses) == 0): break
                else:
                    max_id = tempStatuses[-1].id - 1
                    self.statuses.extend(tempStatuses)
        elif (type(self.userName) == int):
            self.statuses.extend(self.api.GetUserTimeline(user_id=self.userName))
            max_id = self.statuses[-1].id
            while True:
                tempStatuses = self.api.GetUserTimeline(user_id=self.userName, max_id=max_id)
                if (len(tempStatuses) == 0): break
                else:
                    max_id = tempStatuses[-1].id - 1
                    self.statuses.extend(tempStatuses)

    def getMostActiveTime(self):
        times = [0] * 24
        for status in self.statuses:
         # created_at returns a string format of the date/time and the 4th element in that string is the time, and we just want the hour
            time = (int(status.created_at.split()[3].split(":")[0]) + self.userTimeOffset) % 24
            times[time] += 1
        return str(times.index(max(times))) + ":00 to " + str(times.index(max(times)) + 1) + ":00"

    def urlTweetRatio(self):
        numUrls = 0
        for status in self.statuses:
            if (status.urls != []): numUrls += 1
        return "Ratio of tweets with URLs to total: " + str(float(numUrls)/len(self.statuses))

    # top 10 words that are not common
    def topTenWords(self, unique):
        words = dict()
        if (unique):
            for status in self.statuses:
                for word in status.text.split():
                    if (word.lower() in words):
                        words[word.lower()] += 1
                    else:
                        # Doesn't include common words or people user tweets at
                        if (word.lower() not in self.commonWords and list(word)[0] != "@"):
                            words[word.lower()] = 1
        else:
            for status in self.statuses:
                for word in status.text.split():
                    if (word.lower() in words):
                        words[word.lower()] += 1
                    else:
                        # Doesn't include people user tweets at
                        if (list(word)[0] != "@"):
                            words[word.lower()] = 1
        return heapq.nlargest(10, words, key=words.get)

    def favoriteApp(self, web):
        sources = dict()
        if (web):
            for status in self.statuses:

                sourceTemp = " ".join(status.source.split()[2:]).split(">")[1] 
                source = sourceTemp[:len(sourceTemp) - 3]
                if (source in sources):
                    sources[source] += 1
                else:
                    sources[source] = 1
        else:
            for status in self.statuses:
                sourceTemp = " ".join(status.source.split()[2:]).split(">")[1] 
                source = sourceTemp[:len(sourceTemp) - 3]
                if (source in sources):
                    sources[source] += 1
                else:
                    if (source != "Twitter Web Client"):
                        sources[source] = 1
        if (sources == dict()): return "None"
        return heapq.nlargest(1, sources, key=sources.get)[0]

    def happinessScale(self):
        happy = 0 
        negative = 0
        for status in self.statuses:
            for word in status.text.split():
                if (word in self.happyWords): happy += 1
                if (word in self.negativeWords): negative += 1
        if (happy == negative): return 0
        elif (happy > negative): return float(happy) / (happy + negative)
        elif (happy < negative): return -(float(negative) / (happy + negative))

    def help(self):
        print "\nAllowable Commands:\n"
        print "user: returns user_id and screen_name"
        print "mostActiveTime: returns the hour-long range in which the user is usually most active"
        print "friendsAndFollowers: returns how many friends and followers a user has"
        print "urlRatio: returns ratio of tweets that contain links to external sites"
        print "topTenWords: returns top 10 words that user uses"
        print "totalTweets: returns total number of tweets user has tweeted"
        print "favoriteApp: returns the application a user uses most to tweet"
        print "happiness: returns user's overall happiness level based on all tweets (scale from -1 to 1)"
        print "newUser: input new user identifier to gather data about different user"
        print "save: saves the user's data in a text file in root directory of application"
        print "quit: quits the Twitter application\n"

def runTwitter():
    twitter = Twitter()
    twitter.run()
    twitter.help()
    while (True):
        command = raw_input("Enter command('help' for list of available commands): ")
        if (command == "mostActiveTime"):
            print twitter.getMostActiveTime()
        elif (command == "user"):
            print "User ID: " + str(twitter.userID)
            print "Screen name: " + twitter.userScreenName
        elif (command == "friendsAndFollowers"):
            print "Number of friends: " + str(twitter.userFriends)
            print "Number of followers: " + str(twitter.userFollowers)
        elif (command == "urlRatio"):
            print twitter.urlTweetRatio()
        elif (command == "topTenWords"):
            newCommand = raw_input("Do you want to include common words? (y/n): ")
            topTen = []
            if (newCommand == "y"): 
                topTen = twitter.topTenWords(False)
                for i in xrange(10):
                    print str(i + 1) + ". " + topTen[i]
            elif (newCommand == "n"): 
                topTen = twitter.topTenWords(True)
                for i in xrange(10):
                    print str(i + 1) + ". " + topTen[i]
            else: print "Invalid input"
        elif (command == "happiness"):
            print twitter.happinessScale()
        elif (command == "help"):
            twitter.help()
        elif (command == "newUser"):
            twitter.userName = None
            twitter.run()
        elif (command == "totalTweets"):
            print twitter.user.statuses_count
        elif (command == "favoriteApp"):
            newCommand = raw_input("Do you want to include the Twitter Web Client? (y/n): ")
            if (newCommand == "y"): print twitter.favoriteApp(True)
            elif (newCommand == "n"): print twitter.favoriteApp(False)
            else: print "Invalid input"
        elif (command == "save"):
            contents = twitter.userScreenName + " (id:" + str(twitter.userID) + ")\n\n"
            contents += "Friends: " + str(twitter.userFriends) + "\n"
            contents += "Followers: " + str(twitter.userFollowers) + "\n"
            contents += "Total Tweets: " + str(twitter.user.statuses_count) + "\n\n"
            contents += "Most Active Time: " + twitter.getMostActiveTime() + "\n"
            contents += "URL Ratio: " + str(twitter.urlTweetRatio()) + "\n"
            contents += "Favorite App to Tweet From (including web client): " + twitter.favoriteApp(True) + "\n"
            contents += "Favorite App to Tweet From (not including web client): " + twitter.favoriteApp(False) + "\n\n"
            contents += "Top Ten Most Used Words (including common words): " + "\n"
            topTen = twitter.topTenWords(False)
            for i in xrange(10):
                contents += str(i + 1) + ". " + topTen[i] + "\n"
            contents += "\n"
            contents += "Top Ten Most Used Words (not including common words): " + "\n"
            topTen = twitter.topTenWords(True)
            for i in xrange(10):
                contents += str(i + 1) + ". " + topTen[i] + "\n"
            contents += "\n"
            contents += "Overall Happiness Level: " + str(twitter.happinessScale())
            filename = str(twitter.userScreenName) + ".txt"
            with open(filename, "wt") as fout:
                fout.write(contents)        
        elif (command == "quit"):
            break
        else:
            print "Invalid command. Enter 'help' for list of available commands"
