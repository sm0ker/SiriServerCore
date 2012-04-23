#!/usr/bin/python
# -*- coding: utf-8 -*-
# Google units calculator v1.1
# by Mike Pissanos (gaVRos)
#    helpphrase addon by apu95 
#    Usage: simply say Convert or Calculate X to Y
#    Examples: 
#             Convert 70 ferinheight to celsius 
#             Convert 1 euro to dollars
#             Convert 1 tablespoon to teaspoons
#             Calculate 30 divided by 10
#             Calculate 10 plus 11 
#             Calculate 10 minus 1   


import re
import urllib2, urllib
import json

from plugin import *
from plugin import __criteria_key__

from siriObjects.uiObjects import AddViews
from siriObjects.answerObjects import AnswerSnippet, AnswerObject, AnswerObjectLine

class UnitsConverter(Plugin):

    # List of help phrases used by the helpPlugin
    helpPhrases_enUS = ['Convert # <units> to <other unit>', 'Calculate <something>', 'Example 1: Convert 1 Euro to Dollars', 'Example 2: Calculate 30 divided by 10'] 
    
    @register("en-US", "(convert|calculate)* ([\w ]+)")
    @register("en-GB", "(convert|calculate)* ([\w ]+)")
    def defineword(self, speech, language, regex):
        Title = regex.group(regex.lastindex)
        Title = speech.replace('+', 'plus').replace('-', 'minus')
        Query = urllib.quote_plus(Title.encode("utf-8"))
        SearchURL = u'http://www.google.com/ig/calculator?q=' + (str(Query))
        try:
            result = urllib2.urlopen(SearchURL).read().decode("utf-8", "ignore")
            result = re.sub("([a-z]+):", '"\\1" :', result)        
            result = json.loads(result)
            ConvA = result['lhs']
            ConvB = result['rhs'] 
            self.say("Here is what I found..." '\n' +str(ConvA) + " equals, " +str(ConvB))
            self.complete_request()
        except (urllib2.URLError):
            self.say("Sorry, but a connection to the Google calculator could not be established.")
            self.complete_request()
