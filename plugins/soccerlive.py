#!/usr/bin/python
# -*- coding: utf-8 -*-
# original code by hans, modified by Mike (gaVRos) v1.3
# Now supports English US & GB
# Thanks to dogsonmars for helping out ;)
# NOTES: I'm sure someone can take a look at the code and streamline it a bit ;)
# Usage: all football / all soccer will display all live games
#        live football (say team name, country or venue i.e. Champions League)
#        This will parse relavant info
import urllib
import xml.dom.minidom
import random
import re
from xml.dom.minidom import Node

from plugin import *
from siriObjects.answerObjects import AnswerSnippet, AnswerObject, AnswerObjectLine

class fussiPlugin(Plugin):

	@register("en-US", ".*(live football) (.*)|.*(live soccer) (.*)|.*for (.*)|.*games in (.*) today|.*what is the score for (.*)")
	@register("en-GB", ".*(live football) (.*)|.*(live soccer) (.*)|.*for (.*)|.*games in (.*) today|.*what is the score for (.*)")
	def onlyone(self, speech, language, regex):
		searchString = regex.group(regex.lastindex).strip()
		gefunden = 0;
		html = urllib.urlopen("http://www.soccerstand.com/rss/soccer").read()
		dom = xml.dom.minidom.parseString(html)	
                self.say("Let me check my sources...")
		for node in dom.getElementsByTagName('item'):
			sendung = node.getElementsByTagName('title')
			sendeinfo = sendung[0].firstChild.data
			if re.match(".*"+searchString+".*", sendeinfo, re.IGNORECASE):
				gefunden = 1;
				self.say(sendeinfo, sendeinfo.split("(")[0].replace("'","minute").replace("Borussia M'","").replace(" VfB","").replace(" FC","").replace("K'","").replace("1.","").replace("FSV","").replace("Werder ","").replace(" 04"," ").replace(" 05 "," ").replace("VfL","").replace("1. FC","").replace("HSV","HS Fau").replace("(*)", ''))
		if gefunden == 0:
			self.say(u"Sorry I did not find any games for \""+searchString+"\"")
		self.complete_request()
		
        @register("en-US", ".*all .*football.*|.*all .*soccer.*")
        @register("en-GB", ".*all .*football.*|.*all .*soccer.*")
	def onlyall(self, speech, language, regex):
		html = urllib.urlopen("http://www.soccerstand.com/rss/soccer").read()
		dom = xml.dom.minidom.parseString(html)	
                self.say("I found the following games today...")
                sendeinfo = ''
                for node in dom.getElementsByTagName('item'):
                        sendung = node.getElementsByTagName('title')
                        sendeinfo = sendeinfo + sendung[0].firstChild.data + '\n' + '\n'
                        view = AddViews(self.refId, dialogPhase="Completion")
                        ImageAnswer = AnswerObject(title='News for todays games:',lines=[AnswerObjectLine(sendeinfo)])
                        view1 = AnswerSnippet(answers=[ImageAnswer])
                        view.views = [view1]
                self.sendRequestWithoutAnswer(view)
                self.complete_request()
