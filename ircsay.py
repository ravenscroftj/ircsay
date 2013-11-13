import re
import sys
import codecs
import os
import collections
import json
import random

class LogParser:

    startwords = collections.Counter()
    endwords  = collections.Counter()
    unigrams = collections.Counter()
    bigrams  = collections.Counter()

    def __init__(self):
        self.pattern = re.compile("([0-9]{2}:[0-9]{2}) <[@+ ](.+)> (.+)")

        self.msl = 0.0 #mean sentence length
        self.sentcount = 0.0


    def parse(self, filepath):
        
        with codecs.open(filepath,'r', encoding='ascii', errors='replace') as f:

            for line in f.readlines():
                self.parse_line(line)

    def parse_line(self, line):
        
        m = self.pattern.match(line) 

        if(m == None):
            print("Ignoring line %s -not a voice action" % line)
            return


        time = m.group(1)
        user = m.group(2)
        msg  = m.group(3)

        words = msg.split(" ")

        self.sentcount += 1.0

        self.msl = self.msl + ( (len(words)- self.msl) * (1.0 / self.sentcount) )

        self.unigrams.update(words)

        self.startwords[words[0]] += 1
        self.endwords[words[-1]] += 1


        bigrams = [ (words[x], words[x+1]) for x in range(0, len(words)-1) ]

        self.bigrams.update(bigrams)


    def save(self, file):
        """Store the parsed data to disk"""

        with open(file, 'w') as f:

            json.dump({
                "unigrams" : [ (x, self.unigrams[x]) for x in self.unigrams] ,
                "bigrams"  : [ (x,self.bigrams[x]) for x in self.bigrams],
                "startwords" : [(x, self.startwords[x]) for x in self.startwords],
                "endwords"   : [(x, self.endwords[x]) for x in self.endwords],
                "total-sentences" : self.sentcount,
                "mean-sentence-length" : self.msl
                },f)

#------------------------------------------------------------------------------------------------------

class WordStatTool:

    unigrams   = collections.Counter()
    bigrams    = collections.Counter()
    startwords = collections.Counter()
    endwords   = collections.Counter()

    def __init__(self, filename):

        with open(filename,'r') as f:
            loaded = json.load(f)

            ug = { u[0] : u[1] for u in loaded["unigrams"] }
            self.unigrams.update(ug)

            bg = { tuple(b[0]) : b[1] for b in loaded["bigrams"] }
            self.bigrams.update(bg)

            sw = { x[0] : x[1] for x in loaded["startwords"] }
            self.startwords.update(sw)

            ew = { x[0] : x[1] for x in loaded["endwords"] }
            self.endwords.update(ew)

            self.msl = loaded["mean-sentence-length"]

        # done with the file
        

    def word_probability( self, word):
        if not word in self.unigrams:
            return 0.0
        else:
            return self.unigrams[word] / len(self.unigrams)

    def possible_next_words(self, word):

        return [ (b2, (self.bigrams[(w1,b2)] / len(self.bigrams))) for (w1,b2) 
                in self.bigrams if w1 == word]

    def generate_sentence(self):
        """USe randomly chosen words to generate a status"""

        def g(wordno, word):

            finish_chance = max(0, (self.endwords[word] / len(self.endwords)) * ( (wordno - self.msl) / self.msl )   ) 

            r = random.uniform(0,1)

            if( (r <= finish_chance) or (len(self.possible_next_words(word)) < 1) ):
                return ""
            else:
                nw = self.predict_next_word(word)
                return  nw + " " + g(wordno+1, nw)

        first = self.weighted_choice([ (x, self.startwords[x]) for x in self.startwords])

        return first + " " + g(0, first)
        


    def weighted_choice(self, choices):
       total = sum(w for c, w in choices)
       r = random.uniform(0, total)
       upto = 0
       for c, w in choices:
          if upto + w > r:
             return c
          upto += w

       print(choices)
       print(r)
       assert False, "Shouldn't get here"

    def predict_next_word(self, prevword):

        def chance(word, oldchance):

            return oldchance * ( self.unigrams[word] / len(self.unigrams))


        choices = [ (w, chance(w,x)) for (w,x) in self.possible_next_words(prevword)   ] 

        return self.weighted_choice(self.possible_next_words(prevword))


#------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    if(sys.argv[1] == "parse"):

        print("Trying to parse contents of log %s" % sys.argv[2])

        p = LogParser()
        p.parse(sys.argv[2])


        print("Average sentence length is %d" % int(p.msl))

        p.save("output.json")

    else:

        stat = WordStatTool("output.json")


        print(stat.generate_sentence())
