#!/usr/bin/python
# -*- coding: utf-8 -*-
# by Alex 'apexad' Martin
# help from: muhkuh0815 & gaVRos
# added keyword easter eggs: viper88c

import re
import urllib2, urllib
import json
import random
import math

from plugin import *

from siriObjects.baseObjects import AceObject, ClientBoundCommand, ObjectIsCommand, RequestCompleted
from siriObjects.systemObjects import *
from siriObjects.uiObjects import AddViews, AssistantUtteranceView, UIListItem, UIDisambiguationList
from siriObjects.localsearchObjects import Business, MapItem, MapItemSnippet, Rating

googleplaces_api_key = APIKeyForAPI("google")

responses = {
'devel':
    {'de-DE': u"Entschuldigung, aber diese Funktion befindet sich noch in der Entwicklungsphase",
     'en-US': u"Sorry this feature is still under development"
    },
 'select':
    {'de-DE': u"Wen genau?", 
     'en-US': u"What kind of place were you looking for?"
    }
}
speakableDemitter={
'en-US': u", or ",
'de-DE': u', oder '}
notAvailable = None
 
class googlePlacesSearch(Plugin):
     # Dictionary for help phrases used by the helpPlugin
     helpPhrases = {
        "en-US": ["Find|show|where is the nearest|closest|nearby <something>", "Example: Where is the closest gas station?"]
                  }

     @register("en-US", "(find|show|where).* (nearest|nearby|closest) (.*)")
     @register("en-GB", "(find|show|where).* (nearest|nearby|closest) (.*)")
     def googleplaces_search(self, speech, language, regex):
          self.say('Searching...',' ')
          mapGetLocation = self.getCurrentLocation()
          latitude= mapGetLocation.latitude
          longitude= mapGetLocation.longitude
          Title = regex.group(regex.lastindex).strip()
          Query = urllib.quote_plus(str(Title.encode("utf-8")))
          random_results = random.randint(2,15)
          googleurl = "https://maps.googleapis.com/maps/api/place/search/json?location={0},{1}&radius=5000&name={2}&sensor=true&key={3}".format(latitude,longitude,str(Query),str(googleplaces_api_key))
          try:
               jsonString = urllib2.urlopen(googleurl, timeout=20).read()
          except:
               jsonString = None
          if jsonString != None:
               response = json.loads(jsonString)
               if (response['status'] == 'OK') and (len(response['results'])):
                    googleplaces_results = []
                    for result in response['results']:
                         if "rating" in result:
                              avg_rating = result["rating"]
                         else:
                              avg_rating = 0.0
                         rating = Rating(value=avg_rating, providerId='Google Places', count=0)
                         details = Business(totalNumberOfReviews=0,name=result['name'],rating=rating)
                         if (len(googleplaces_results) < random_results):
                              mapitem = MapItem(label=result['name'], street=result['vicinity'], latitude=result['geometry']['location']['lat'], longitude=result['geometry']['location']['lng'])
                              mapitem.detail = details
                              googleplaces_results.append(mapitem)
                         else:
                              break
                    mapsnippet = MapItemSnippet(items=googleplaces_results)
                    count_min = min(len(response['results']),random_results)
                    count_max = max(len(response['results']),random_results)
                    view = AddViews(self.refId, dialogPhase="Completion")
                    view.views = [AssistantUtteranceView(speakableText='I found '+str(count_max)+' '+str(Title)+' results... '+str(count_min)+' of them are fairly close to you:', dialogIdentifier="googlePlacesMap"), mapsnippet]
                    self.sendRequestWithoutAnswer(view)
               else:
                   self.say("I'm sorry but I did not find any results for "+str(Title)+" near you!")
          else:
               self.say("I'm sorry but I did not find any results for "+str(Title)+" near you!")
          self.complete_request()
          
     def GooglePlaceSearch(self, speech, language, Title):
          self.say('Searching...',' ')
          global notAvailable
          mapGetLocation = self.getCurrentLocation()
          latitude= mapGetLocation.latitude
          longitude= mapGetLocation.longitude
          Query = urllib.quote_plus(Title)
          random_results = random.randint(2,15)
          googleurl = "https://maps.googleapis.com/maps/api/place/search/json?location={0},{1}&radius=5000&name={2}&sensor=true&key={3}".format(latitude,longitude,str(Query),str(googleplaces_api_key))
          try:
               jsonString = urllib2.urlopen(googleurl, timeout=20).read()
          except:
               jsonString = None
          if jsonString != None:
               response = json.loads(jsonString)
               if (response['status'] == 'OK') and (len(response['results'])):
                    googleplaces_results = []
                    for result in response['results']:
                         if "rating" in result:
                              avg_rating = result["rating"]
                         else:
                              avg_rating = 0.0
                         rating = Rating(value=avg_rating, providerId='Google Places', count=0)
                         details = Business(totalNumberOfReviews=0,name=result['name'],rating=rating)
                         if (len(googleplaces_results) < random_results):
                              mapitem = MapItem(label=result['name'], street=result['vicinity'], latitude=result['geometry']['location']['lat'], longitude=result['geometry']['location']['lng'])
                              mapitem.detail = details
                              googleplaces_results.append(mapitem)
                         else:
                              break
                    mapsnippet = MapItemSnippet(items=googleplaces_results)
                    count_min = min(len(response['results']),random_results)
                    count_max = max(len(response['results']),random_results)
                    view = AddViews(self.refId, dialogPhase="Completion")
                    view.views = [AssistantUtteranceView(speakableText='I found '+str(count_max)+' '+str(Title)+' results... '+str(count_min)+' of them are fairly close to you:', dialogIdentifier="googlePlacesMap"), mapsnippet]
                    self.sendRequestWithoutAnswer(view)
               else:
                   if notAvailable != None:
                       self.say(notAvailable)
                   else:
                       self.say("I'm sorry but I did not find any results for "+str(Title)+" near you!")
          else:
               if notAvailable != None:
                   self.say(notAvailable)
               else:
                  self.say("I'm sorry but I did not find any results for "+str(Title)+" near you!")
          notAvailable = None
          self.complete_request()


     @register("en-US", ".*bury.*dead.*body.*"")
     @register("en-GB", "(find|show|where).* (hide).* (dead|body|corpse)")
     def googleplaces_body(self, speech, language, regex):
         root = UIAddViews(self.refId)
         root.dialogPhase = root.DialogPhaseClarificationValue
         utterance = UIAssistantUtteranceView()
         utterance.text = responses['select'][language]
         utterance.speakableText = responses['select'][language] 
         utterance.listenAfterSpeaking = True
         root.views = [utterance]
         # create a list with all the possibilities 
         lst = UIDisambiguationList()
         lst.items = []
         lst.speakableSelectionResponse = "OK!"
         lst.listenAfterSpeaking = True
         lst.selectionResponse = "OK"
         listPlaces = ['Swamps', 'Reservoirs', 'Lakes', 'Dumps', 'Mines', 'Churches']
         root.views.append(lst)
         for gPlac in listPlaces:
             item = UIListItem()
             item.selectionResponse = gPlac
             item.selectionText = gPlac
             item.title = gPlac
             item.commands = [SendCommands(commands=[StartRequest(handsFree=False, utterance=gPlac)])]
             lst.items.append(item)
         answer = self.getResponseForRequest(root)
         print answer
         if answer == listPlaces[0]:
             Title = listPlaces[0]
         if answer == listPlaces[1]:
             Title = listPlaces[1]            
         if answer == listPlaces[2]:
             Title = listPlaces[2]
         if answer == listPlaces[3]:
             Title = listPlaces[3]
         if answer == listPlaces[4]:
             Title = listPlaces[4]
         self.GooglePlaceSearch(speech, language, Title) 

     @register('en-US', "(I'm).*(hungry)")
     def search_im_hungry(self, speech, language):
          Title = "restaurants"
          self.GooglePlaceSearch(speech, language, Title) 
          
     @register("en-US", "(find|show|where).* (drugs|cocaine|meth|speed|heroin|LSD|ecstasy|opium|marijuana|weed|shrooms|pcp)|(want|need|must get|must have).* (drugs|cocaine|meth|speed|heroin|LSD|ecstasy|opium|marijuana|weed|shrooms|pcp)")
     @register("en-GB", "(find|show|where).* (drugs|cocaine|meth|speed|heroin|LSD|ecstasy|opium|marijuana|weed|shrooms|pcp)|(want|need|must get|must have).* (drugs|cocaine|meth|speed|heroin|LSD|ecstasy|opium|marijuana|weed|shrooms|pcp)")
     def googleplaces_drugs(self, speech, language, regex):
           global notAvailable
           notAvailable = "I'm sorry but I did not find any Addiction Treatment Centers close by. Please stop asking me to find drug dealers"
           Title = "Addiction Treatment Centers"
           self.GooglePlaceSearch(speech, language, Title) 
           
     @register("en-US", ".*murder.*|.*kill.*")
     @register("en-GB", ".*murder.*|.*kill.*")
     def googleplaces_murder(self, speech, language, regex):
           global notAvailable
           notAvailable = "I'm sorry but I did not find any mental health clinics close by. Please go see your therapist A.S.A.P."
           Title = "Mental Health clinics"
           self.GooglePlaceSearch(speech, language, Title) 
     
     @register('en-US', "(I).* (want|wanna|need|must get|must have).* (drunk|wasted|alcohol|adult drink)")
     def googleplaces_adult_drink(self, speech, language):
          global notAvailable
          answer = ["alcohol anonymous", "liquor stores"]
          Title = random.choice(answer)
          if Title == "alcohol anonymous":
              notAvailable = "I'm sorry but I did not find any Alcoholics Anonymous locations close by. Please seek help for your addiction"
          self.GooglePlaceSearch(speech, language, Title) 
          
     @register('en-US', "(I).* (want|wanna|need|must get|must have).* (laid|sex)")
     def googleplaces_laid(self, speech, language):
          global notAvailable
          answer = ["escort services", "sex addiction therapist"]
          Title = random.choice(answer)
          if Title == "sex addiction therapist":
              notAvailable = "I'm sorry but I did not find any sex addiction therapists close by. Please seek help for your addiction"
          elif Title == "escort services":
              notAvailable = "I'm sorry but I did not find any hookers close by. Please go get someone of your own to do that with." 
          self.GooglePlaceSearch(speech, language, Title) 
          
     @register('en-US', "(I'm|I).* (tired)| (sleepy)")
     def googleplaces_sleep(self, speech, language):
          answer = ["hotels", "motels", "talk"]
          place = random.choice(answer)
          if place == "talk":
              answerTalk = ["I hope you are not driving a car right now!", "Listen to me, put down the iphone right now and take a nap. I will be here when you get back."]
              self.say(random.choice(answerTalk))
          else:
              Title = place
              self.GooglePlaceSearch(speech, language, Title) 
    
