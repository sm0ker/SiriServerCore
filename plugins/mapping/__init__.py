#!/usr/bin/env python
# encoding: utf-8
"""
Mapping Plugins for SiriServerCore
Created by Javik
"""
import re
import urllib2, urllib
import json
from plugin import *
from siriObjects.systemObjects import *
from siriObjects.uiObjects import *
from siriObjects.localsearchObjects import MapItem, MapItemSnippet, ShowMapPoints
from siriObjects.uiObjects import AddViews, AssistantUtteranceView
from siriObjects.baseObjects import *
from siriObjects.contactObjects import *


class Mapping(Plugin):
	@register("en-US", "(Where is) (.*)")
	@register("en-GB", "((Where is) (.*))")
	def whereis(self, speech, language, regex):
	     self.say('Searching...',' ')
	     Title = regex.group(regex.lastindex).strip()    
	     Query = urllib.quote_plus(str(Title.encode("utf-8")))
	     googleurl = "http://maps.googleapis.com/maps/api/geocode/json?address={0}&sensor=true&language=en".format(Query)
	     jsonString = urllib2.urlopen(googleurl, timeout=20).read()
	     response = json.loads(jsonString)
	     if (response['status'] == 'OK') and (len(response['results'])):
	       googleplaces_results = []
	       for result in response['results']:
	           label = "{0}".format(Title.title())
	           street =result['formatted_address']
	           latitude=result['geometry']['location']['lat']
	           longitude=result['geometry']['location']['lng']
           
	           mapitem = MapItem(label=label, street=street, latitude=latitude, longitude=longitude)
	           googleplaces_results.append(mapitem)
	           mapsnippet = MapItemSnippet(items=googleplaces_results)
	           view = AddViews(self.refId, dialogPhase="Completion")
	           view.views = [AssistantUtteranceView(speakableText='Showing {0} on the map...'.format(Title.title()), dialogIdentifier="googlePlacesMap"), mapsnippet]
	           self.sendRequestWithoutAnswer(view)
	           self.complete_request()
	     else:
	       self.say("Sorry, I couldn't find that location...")
	       self.complete_request()
       
	@register("en-US", "(Where am I.*)|(Where are we.*)")
	@register("en-GB", "(Where am I.*)|(Where are we.*)")
	def whereami(self, speech, language, regex):
	     self.say('Searching...',' ')
	     mapGetLocation = self.getCurrentLocation(force_reload=True,accuracy=GetRequestOrigin.desiredAccuracyBest)
	     latitude= mapGetLocation.latitude
	     longitude= mapGetLocation.longitude
	     googleurl = "http://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&sensor=true".format(latitude, longitude)
	     jsonString = urllib2.urlopen(googleurl, timeout=20).read()
	     response = json.loads(jsonString)
	     if (response['status'] == 'OK') and (len(response['results'])):
	       googleplaces_results = []
	       for result in response['results']:
	           label = "Your location"
	           street =result['formatted_address']
	           mapitem = MapItem(label=label, street=street, latitude=latitude, longitude=longitude)
	           googleplaces_results.append(mapitem)
	           mapsnippet = MapItemSnippet(items=googleplaces_results)
	           view = AddViews(self.refId, dialogPhase="Completion")
	           view.views = [AssistantUtteranceView(speakableText='Showing your location on the map...', dialogIdentifier="googlePlacesMap"), mapsnippet]
	           self.sendRequestWithoutAnswer(view)
	           self.complete_request()
	     else:
	       self.say("Sorry, I couldn't find you...")
	       self.complete_request()

	@register("en-US", ".*traffic like (in|on) (?P<location>[\w ]+?)$")
	@register("en-GB", ".*traffic like (in|on) (?P<location>[\w ]+?)$")
	def traffic(self, speech, language, regex):
	   searchlocation = regex.group('location')
	   Title = searchlocation   
	   Query = urllib.quote_plus(str(Title.encode("utf-8")))
	   googleurl = "http://maps.googleapis.com/maps/api/geocode/json?address={0}&sensor=true&language=en".format(Query)
	   jsonString = urllib2.urlopen(googleurl, timeout=20).read()
	   response = json.loads(jsonString)
	   if (response['status'] == 'OK') and (len(response['results'])):
	     for result in response['results']:
	         label = "{0}".format(Title.title())
	         latitude=result['geometry']['location']['lat']
	         longitude=result['geometry']['location']['lng']
	         city=result['address_components'][0]['long_name']
	         state=result['address_components'][2]['short_name']
	         country=result['address_components'][3]['short_name']
	   code = 0
	   Loc = Location(self.refId)
	   Loc.street = ""
	   Loc.countryCode = country
	   Loc.city = city
	   Loc.latitude = latitude
	   Loc.stateCode = state
	   Loc.longitude = longitude
	   Map = MapItem(self.refId)
	   Map.detailType = "ADDRESS_ITEM"
	   Map.label = label
	   Map.location = Loc
	   Source = MapItem(self.refId)
	   Source.detailType = "CURRENT_LOCATION"
	   ShowPoints = ShowMapPoints(self.refId)
	   ShowPoints.showTraffic = True  
	   ShowPoints.showDirections = False
	   ShowPoints.regionOfInterestRadiusInMiles = "10.0"
	   ShowPoints.itemDestination = Map
	   ShowPoints.itemSource = Source
	   AddViews = UIAddViews(self.refId)
	   AddViews.dialogPhase = "Summary"
	   AssistantUtteranceView = UIAssistantUtteranceView()
	   AssistantUtteranceView.dialogIdentifier = "LocationSearch#foundLocationForTraffic"
	   AssistantUtteranceView.speakableText = "Here\'s the traffic:"
	   AssistantUtteranceView.text = "Here\'s the traffic:"
	   AddViews.views = [(AssistantUtteranceView)]
	   AddViews.scrollToTop = False
	   AddViews.callbacks = [ResultCallback([ShowPoints], code)]
	   callback = [ResultCallback([AddViews])]
	   self.complete_request(callbacks=[ResultCallback([AddViews], code)])

	@register("en-US", ".*traffic like")
	@register("en-GB", ".*traffic like")
	def trafficSelf(self, speech, language, regex):
	   mapGetLocation = self.getCurrentLocation(force_reload=True,accuracy=GetRequestOrigin.desiredAccuracyBest)
	   latitude= mapGetLocation.latitude
	   longitude= mapGetLocation.longitude
	   label = "Your location"
	   code = 0
	   Loc = Location(self.refId)
	   Loc.street = ""
	   Loc.countryCode = "US"
	   Loc.city = ""
	   Loc.latitude = latitude
	   Loc.stateCode = ""
	   Loc.longitude = longitude
	   Map = MapItem(self.refId)
	   Map.detailType = "ADDRESS_ITEM"
	   Map.label = label
	   Map.location = Loc
	   Source = MapItem(self.refId)
	   Source.detailType = "CURRENT_LOCATION"
	   ShowPoints = ShowMapPoints(self.refId)
	   ShowPoints.showTraffic = True  
	   ShowPoints.showDirections = False
	   ShowPoints.regionOfInterestRadiusInMiles = "10.0"
	   ShowPoints.itemDestination = Map
	   ShowPoints.itemSource = Source
	   AddViews = UIAddViews(self.refId)
	   AddViews.dialogPhase = "Summary"
	   AssistantUtteranceView = UIAssistantUtteranceView()
	   AssistantUtteranceView.dialogIdentifier = "LocationSearch#foundLocationForTraffic"
	   AssistantUtteranceView.speakableText = "Here\'s the traffic:"
	   AssistantUtteranceView.text = "Here\'s the traffic:"
	   AddViews.views = [(AssistantUtteranceView)]
	   AddViews.scrollToTop = False
	   AddViews.callbacks = [ResultCallback([ShowPoints], code)]
	   callback = [ResultCallback([AddViews])]
	   self.complete_request(callbacks=[ResultCallback([AddViews], code)])

	@register("en-US", "(How do I get( to)?|.*directions( to?)) ((?P<userlocation>(home|work|school))|(?P<location>[\w ]+))")
	@register("en-GB", "(How do I get( to)?|.*directions( to?)) ((?P<userlocation>(home|work|school))|(?P<location>[\w ]+))")
	def traffic(self, speech, language, regex):
	   if regex.group('userlocation'):
	       locationType = regex.group('userlocation').capitalize()
	       label = locationType.title()
	       if locationType == "Work" or locationType == "Home":
	           locationType = "_$!<{0}>!$_".format(locationType)
	       meSearch = ABPersonSearch(self.refId)
	       meSearch.me = True
	       meSearch.scope = "Local"
	       answer = self.getResponseForRequest(meSearch)
	       if ObjectIsCommand(answer, ABPersonSearchCompleted):
	           results = ABPersonSearchCompleted(answer)
	           persons = results.results
	           identfind = results.results[0]
	       contactIdentifier = identfind.identifier
	       me = persons[0]
	       Addresses = filter(lambda x: x.label == locationType, me.addresses)
	       if len(Addresses) > 0:
	           Result = Addresses[0]
	           street = Result.street
	           PostalCode = Result.postalCode
	           city = Result.city
	           Title = "{0}, {1}, {2}".format(street, city, PostalCode)
	           Query = urllib.quote_plus(str(Title.encode("utf-8")))
	           googleurl = "http://maps.googleapis.com/maps/api/geocode/json?address={0}&sensor=true".format(Query)
	           jsonString = urllib2.urlopen(googleurl, timeout=20).read()
	           response = json.loads(jsonString)
	           if (response['status'] == 'OK') and (len(response['results'])):
	               for result in response['results']:
	                   latitude=result['geometry']['location']['lat']
	                   longitude=result['geometry']['location']['lng']
	                   state=result['address_components'][4]['long_name']
	       else: 
	           self.say("Sorry, I couldn't find {0} in your address book".format(label))
	           self.complete_request()
	   else:
	       searchlocation = regex.group('location')
	       Title = searchlocation   
	       Query = urllib.quote_plus(str(Title.encode("utf-8")))
	       googleurl = "http://maps.googleapis.com/maps/api/geocode/json?address={0}&sensor=true&language=en".format(Query)
	       jsonString = urllib2.urlopen(googleurl, timeout=20).read()
	       response = json.loads(jsonString)
	       label = Title.title()
	       if (response['status'] == 'OK') and (len(response['results'])):
	         response = response['results'][0]
	         label = "{0}".format(Title.title())
	         latitude=response['geometry']['location']['lat']
	         longitude=response['geometry']['location']['lng']
	         city=response['address_components'][0]['long_name']
	         state=response['address_components'][2]['short_name']
	         country="US"
	         street=""
	       else:
	         random_results = random.randint(2,15)
	         mapGetLocation = self.getCurrentLocation(force_reload=True,accuracy=GetRequestOrigin.desiredAccuracyBest)
	         latitude= mapGetLocation.latitude
	         longitude= mapGetLocation.longitude
	         yelpurl = "http://api.yelp.com/business_review_search?term={0}&lat={1}&long={2}&radius=10&limit=10&ywsid={3}".format(Query, latitude, longitude, yelp_api_key)
	         try:
	           jsonString = urllib2.urlopen(yelpurl, timeout=20).read()
	         except:
	           jsonString = None
	         if jsonString != None:
	           response = json.loads(jsonString)
	           if (response['message']['text'] == 'OK') and (len(response['businesses'])):
	               sortedResults = sorted(response['businesses'], key=lambda business: float(business['distance']))
	               response = response['businesses']
	               sortedResults = sortedResults[0]
	               label = sortedResults['name']
	               latitude = sortedResults['latitude']
	               longitude = sortedResults['longitude']
	               state = sortedResults['state']
	               street = sortedResults['address1']
	               city = sortedResults['city']
	           else:
	               self.say("I'm sorry but I did not find any results for "+str(Title)+" near you!")
	               self.complete_request()

	   code = 0
	   Loc = Location(self.refId)
	   Loc.street = street
	   Loc.countryCode = "US"
	   Loc.city = city
	   Loc.latitude = latitude
	   Loc.stateCode = state
	   Loc.longitude = longitude
	   Map = MapItem(self.refId)
	   Map.detailType = "ADDRESS_ITEM"
	   Map.label = label
	   Map.location = Loc
	   Source = MapItem(self.refId)
	   Source.detailType = "CURRENT_LOCATION"
	   ShowPoints = ShowMapPoints(self.refId)
	   ShowPoints.showTraffic = False  
	   ShowPoints.showDirections = True
	   ShowPoints.regionOfInterestRadiusInMiles = "10.0"
	   ShowPoints.itemDestination = Map
	   ShowPoints.itemSource = Source
	   AddViews = UIAddViews(self.refId)
	   AddViews.dialogPhase = "Summary"
	   AssistantUtteranceView = UIAssistantUtteranceView()
	   AssistantUtteranceView.dialogIdentifier = "LocationSearch#foundLocationForDirections"
	   AssistantUtteranceView.speakableText = "Here are directions to {0}:".format(label)
	   AssistantUtteranceView.text = "Here are directions to {0}:".format(label)
	   AddViews.views = [(AssistantUtteranceView)]
	   AddViews.scrollToTop = False
	   AddViews.callbacks = [ResultCallback([ShowPoints], code)]
	   callback = [ResultCallback([AddViews])]
	   self.complete_request(callbacks=[ResultCallback([AddViews], code)])