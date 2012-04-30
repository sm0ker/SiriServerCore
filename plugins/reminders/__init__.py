#!/usr/bin/python
# -*- coding: utf-8 -*-

#Reminder Plugin by Javik
#For SiriServerCore
import pytz
from pytz import timezone
from plugin import *
from siriObjects.baseObjects import ObjectIsCommand
from siriObjects.contactObjects import ABPersonSearch, ABPersonSearchCompleted
from siriObjects.reminderObjects import *
from siriObjects.systemObjects import SendCommands, StartRequest, \
    PersonAttribute, Person, DomainObjectCreate, DomainObjectCreateCompleted, \
    DomainObjectUpdate, DomainObjectUpdateCompleted, DomainObjectRetrieve, \
    DomainObjectRetrieveCompleted, DomainObjectCommit, DomainObjectCommitCompleted, \
    DomainObjectCancel, DomainObjectCancelCompleted, Location
from siriObjects.uiObjects import UIConfirmationOptions, ConfirmSnippet, UIConfirmSnippet, UICancelSnippet
from datetime import *
import random
import urllib2, urllib
import json

pmWords = ["pm", "tonight"]
amWords = ["am", "in the morning"]

responses = {
'cantUnderstand': 
    {'en-US': [u"Sorry, I did not understand, please try again", u"Sorry, I don't know what you want"]
     },
'queryReminderTime':
    {'en-US': [u"When should I remind you?", u"When would you like to be reminded?"]
     },
'showUpdatedReminder': 
    {'en-US': [u"I updated your reminder. Ready to create it?", u"Ok, I got that, do you want to create it?", u"Thanks, do you want to create it now?"]
     },
'cancelReminder': 
    {'en-US': [u"Ok, I won't remind you.", u"Ok, I deleted it."]
     },
'cancelFail':
    {'en-US': [u"Sorry I could not properly cancel your reminder"]
     },
'createReminderFail':
    {'en-US': [u"Oops, looks like something went wrong, please try again later, sorry!"]
     },
'Remind':
    {'en-US': [u"Ok, I'll remind you!", u"Ok, I've created the reminder"]
     },
'RemindFail':
    {'en-US': [u"Something seems to have gone wrong, I could not create your reminder"]
     },
'clarification':
    {'en-US': [u"Would you like to cancel, or change it?"]
     }
}

questions = {
'answerCREATE': 
    {'en-US': ['yes', 'send', 'yep', 'sure', 'do it', 'yeah', 'okay', 'ok']
     },
'answerCANCEL':
    {'en-US': ['cancel', 'no', 'delete', 'nope', 'abort']
     },
}

snippetButtons = {
'denyText':
    {'de-DE': "Cancel",
     'en-US': "Cancel"
     },
'cancelLabel':
    {'de-DE': "Cancel",
     'en-US': "Cancel"
     },
'submitLabel':
    {'de-DE': "Confirm",
     'en-US': "Confirm"
     },
'confirmText':
    {'de-DE': "Confirm",
     'en-US': "Confirm"
     },
'cancelTrigger':
    {'de-DE': "Deny",
     'en-US': "Deny"
     }
}

speakableDemitter={
'en-US': u", or ",
'de-DE': u', oder '}

class Reminders(Plugin):
    
    def locationFind(self, locationType):
        print locationType      
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
            Street = Result.street
            PostalCode = Result.postalCode
            City = Result.city
            Title = "{0}, {1}, {2}".format(Street, City, PostalCode)
            Query = urllib.quote_plus(str(Title.encode("utf-8")))
            googleurl = "http://maps.googleapis.com/maps/api/geocode/json?address={0}&sensor=true".format(Query)
            jsonString = urllib2.urlopen(googleurl, timeout=20).read()
            response = json.loads(jsonString)
            if (response['status'] == 'OK') and (len(response['results'])):
                for result in response['results']:
                    latitude=result['geometry']['location']['lat']
                    longitude=result['geometry']['location']['lng']
                    stateCode=result['address_components'][4]['long_name']
                    countryCode=result['address_components'][5]['long_name']
                    Location = [latitude, longitude, Street, City, PostalCode, stateCode, countryCode, contactIdentifier]
                    return Location
        else: 
            return


    def herefind(self):
          mapGetLocation = self.getCurrentLocation(force_reload=True,accuracy=GetRequestOrigin.desiredAccuracyBest)
          latitude= mapGetLocation.latitude
          longitude= mapGetLocation.longitude
          googleurl = "http://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&sensor=true".format(latitude, longitude)
          jsonString = urllib2.urlopen(googleurl, timeout=20).read()
          response = json.loads(jsonString)
          if (response['status'] == 'OK') and (len(response['results'])):
            googleplaces_results = []
            for result in response['results']:
              result = response['results'][0]
              formattedaddress=result['formatted_address']
              formattedaddress=formattedaddress.replace(',','')
              split = formattedaddress.rsplit()
              Street = split[0] + " " + split[1] + " " + split[2]
              City = split[3]
              PostalCode = split[5]
              stateCode = split[4]
              countryCode = split[6]
              Location = [latitude, longitude, Street, City, PostalCode, stateCode, countryCode]
              return Location
          else:
            return
    
    def finalCommit(self, reminder, language):
        
        commitCMD = DomainObjectCommit(self.refId)
        commitCMD.identifier = ReminderObject()
        commitCMD.identifier.identifier = reminder.identifier
        
        answer = self.getResponseForRequest(commitCMD)
        if ObjectIsCommand(answer, DomainObjectCommitCompleted):
            answer = DomainObjectCommitCompleted(answer)
            reminder.identifier = answer.identifier
            lists = ReminderListObject()
            lists.name = "Reminders"
            reminder.lists = lists
            createAnchor = UIAddViews(self.refId)
            createAnchor.dialogPhase = createAnchor.DialogPhaseConfirmedValue
            askCreateView = UIAssistantUtteranceView()
            askCreateView.dialogIdentifier = "CreateReminder#createdReminder"
            askCreateView.text = askCreateView.speakableText = random.choice(responses['Remind'][language])
            askCreateView.listenAfterSpeaking = False
            snippet = ReminderSnippet()
            snippet.reminders = [reminder]
            createAnchor.views = [askCreateView, snippet]
            self.sendRequestWithoutAnswer(createAnchor)
            self.complete_request()
        else:
            self.say(random.choice(responses['RemindFail'][language]))
            self.complete_request()
            
            
    def createReminderSnippet(self, reminder, addConfirmationOptions, dialogIdentifier, text, language):
        createAnchor = UIAddViews(self.refId)
        createAnchor.dialogPhase = createAnchor.DialogPhaseConfirmationValue

        askCreateView = UIAssistantUtteranceView()
        askCreateView.dialogIdentifier = dialogIdentifier
        askCreateView.text = askCreateView.speakableText = text
        askCreateView.listenAfterSpeaking = True
        
        snippet = ReminderSnippet()
        if addConfirmationOptions:
            
            conf = UIConfirmSnippet({})
            conf.requestId = self.refId
            
            confOpts = UIConfirmationOptions()
            confOpts.submitCommands = [SendCommands([conf, StartRequest(False, "^reminderConfirmation^=^yes^")])]
            confOpts.confirmCommands = confOpts.submitCommands
            
            cancel = UICancelSnippet({})
            cancel.requestId = self.refId
            
            confOpts.cancelCommands = [SendCommands([cancel, StartRequest(False, "^reminderConfirmation^=^cancel^, ^no^")])]
            confOpts.denyCommands = confOpts.cancelCommands
            
            confOpts.denyText = snippetButtons['denyText'][language]
            confOpts.cancelLabel = snippetButtons['cancelLabel'][language]
            confOpts.submitLabel = snippetButtons['submitLabel'][language]
            confOpts.confirmText = snippetButtons['confirmText'][language]
            confOpts.cancelTrigger = snippetButtons['cancelTrigger'][language]
            
            snippet.confirmationOptions = confOpts
            
        snippet.reminders = [reminder]
        createAnchor.views = [askCreateView, snippet]
        return createAnchor
            
    def createNewReminder(self, content, correctTime, timetype, EndDate):
        tz = timezone(self.connection.assistant.timeZoneId)
        ##print EndDate
        ##print correctTime
        if timetype == "Relative":
            trig = ReminderDateTimeTrigger()
            trig.timeZoneId = self.connection.assistant.timeZoneId
            trig.date = EndDate
            x = ReminderObject()
            x.trigger = trig
            x.important = False
            x.completed = False
            x.subject = content.capitalize().strip("in")
            x.dueDate = EndDate
            x.dueDateTimeZoneId = trig.timeZoneId
            
        if timetype == "Hour":
            trig = ReminderDateTimeTrigger()
            trig.timeZoneId = self.connection.assistant.timeZoneId
            trig.date = correctTime
            x = ReminderObject()
            x.important = False
            x.completed = False
            x.subject = content.capitalize().strip("at")
            x.trigger = trig
            x.dueDate = correctTime
            x.dueDateTimeZoneId = trig.timeZoneId
            
        if timetype[0] == "Location":
            if timetype[1] == "Arrival":
                ArriveDepart = "OnArrival"
            if timetype[1] == "Departure":
                ArriveDepart = "OnDeparture"
            x = None
            
            if correctTime == "Here":
                x = self.herefind()
                identifier = None
            else:
                x = self.locationFind(correctTime)
                identifier = x[7]
            if x != None:
                print x
                Loc = Location()
                Loc.street = x[2]
                Loc.countryCode = x[6]
                Loc.city = x[3]
                Loc.label = correctTime
                Loc.postalCode = x[4]
                Loc.latitude = x[0]
                Loc.stateCode = x[5]
                Loc.longitude = x[1]
                Loc.accuracy = "10.0"
                trig = ReminderLocationTrigger()
                trig.contactIdentifier = identifier
                trig.timing = ArriveDepart
                trig.location = Loc
                x = ReminderObject()
                x.important = False
                x.completed = False
                x.subject = content.capitalize().strip("at")
                x.trigger = trig        
            else:
                self.say("Sorry, I couldn't find that location in your contact card")
                self.complete_request()
            
        answer = self.getResponseForRequest(DomainObjectCreate(self.refId, x))
        if ObjectIsCommand(answer, DomainObjectCreateCompleted):
            answer = DomainObjectCreateCompleted(answer)
            x = ReminderObject()
            x.identifier = answer.identifier
            return x
        else:
            return None
    def createnewremindernoinfo(self, content):
        x = ReminderObject()
        x.important = False
        x.completed = False
        x.subject = content
        answer = self.getResponseForRequest(DomainObjectCreate(self.refId, x))
        if ObjectIsCommand(answer, DomainObjectCreateCompleted):
            answer = DomainObjectCreateCompleted(answer)
            x = ReminderObject()
            x.identifier = answer.identifier
            return x
        else:
            return None
    def getReminderIdentifier(self, identifier):
        retrieveCMD = DomainObjectRetrieve(self.refId)
        x = ReminderObject()
        x.identifier = identifier
        retrieveCMD.identifiers = [x]
        answer = self.getResponseForRequest(retrieveCMD)
        if ObjectIsCommand(answer, DomainObjectRetrieveCompleted):
            answer = DomainObjectRetrieveCompleted(answer)
            result = ReminderObject()
            result.initializeFromPlist(answer.objects[0].to_plist())
            return result
        else:
            return None
        
    def askAndSetTime(self, reminder, language):
        tz = timezone(self.connection.assistant.timeZoneId)
        x = datetime.now(tz)
        pmWords = ["pm", "tonight"]
        amWords = ["am"]
        correctTime = None
        State = "noTime"
        Satisfied = False
        while not Satisfied:
            createAnchor = self.createReminderSnippet(reminder, False, "Createreminder#reminderMissingTime", random.choice(responses['queryReminderTime'][language]), language)
            answer = self.getResponseForRequest(createAnchor)
            relativematch = re.match('in ((?P<relative>(?P<relativeinteger>([0-9/ ])*|in||a|an|the)\s+(?P<relativeunits>(minutes?|hrs?|hours?|days?|weeks?))))', answer, re.IGNORECASE)
            if relativematch is not None:
                State = "Time"
                Satisfied = True
                print "relativefound"
                timetype = "Relative"
                relativeint = relativematch.group('relativeinteger')
                relativeunit = relativematch.group('relativeunits').strip("s").title()
                if relativeunit == "Minute":
                    z = int(relativeint) * 60
                    correctTime = x + timedelta(seconds=z)
                if relativeunit == "Hour":
                    z = int(relativeint) * 60 * 60
                    correctTime = x + timedelta(seconds=z)
                if relativeunit == "Day":
                    z = int(relativeint) * 24 * 60 * 60
                    correctTime = x + timedelta(seconds=z)
                if relativeunit == "Week":
                    z = int(relativeint) * 7 * 24 * 60 * 60
                    correctTime = x + timedelta(seconds=z)
                
            weekdaymatch = re.match('(?P<weekday>on (?P<dayofweek>(monday?|tuesday?|wednesday?|thursday?|friday?|saturday?|sunday?)) at ((?P<weekdayhour>([0-9]{1,4}):?\s*([0-9]{2})?\s*)(?P<weekdayampm>(am|pm))?|noon|midnight)(\s|$))', answer, re.IGNORECASE)
            if weekdaymatch is not None:
                State = "Time"
                Satisfied = True
                timetype = "Hour"
                dayofweek = weekdaymatch.group('dayofweek')
                parsehour = weekdaymatch.group('weekdayhour')
                hour = weekdaymatch.group('weekdayhour')
                timehint = weekdaymatch.group('weekdayampm')
                if dayofweek == "monday":
                    dayofweek = 1
                if dayofweek == "tuesday":
                    dayofweek = 2
                if dayofweek == "wednesday":
                    dayofweek = 3
                if dayofweek == "thursday":
                    dayofweek = 4
                if dayofweek == "friday":
                    dayofweek = 5
                if dayofweek == "saturday":
                    dayofweek = 6
                if dayofweek == "sunday":
                    dayofweek = 7
                if timehint == "":
                    if int(hour) > 1259:
                        sethour = parsehour[0:2]
                        minutes = parsehour[2:4]
                        correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                    else:
                        if 2 < len(hour) < 4:
                            sethour = parsehour[0:1]
                            minutes = parsehour[1:3]
                            correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                        if len(hour) > 3:
                            sethour = parsehour[0:2]
                            minutes = parsehour[2:4]
                            correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                        if len(hour) == 1:
                            sethour = parsehour[0:1]
                            correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                        if len(hour) == 2:
                            print "yay"
                            sethour = parsehour[0:2]
                            correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                if len(str(hour)) < 4:
                    for pmhints in pmWords:
                        if pmhints in timehint:
                            if int(hour) == 12:
                                correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                            if int(hour) != 12:
                                hour = int(hour) + 12
                                correctTime = x.replace(hour=hour, minute=0, second=0, microsecond=0)
                    for amhints in amWords:
                        if amhints in timehint:
                            if int(hour) == 12:
                                correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                            if int(hour) != 12:
                                correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                if len(str(hour)) > 3:
                    if len(str(hour)) == 4:
                        hour = parsehour[0]
                        minutes = parsehour[1:3]
                    if len(str(hour)) == 5:
                        hour = parsehour[0:2]
                        minutes = parsehour[2:4]
                    x = datetime.now(tz)
                    for pmhints in pmWords:
                        if pmhints in timehint:
                            if int(hour) == 12:
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                            if int(hour) != 12:
                                hour = int(hour) + 12
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                    for amhints in amWords:
                        if amhints in timehint:
                            if int(hour) == 12:
                                correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                            if int(hour) != 12:
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                if x.isoweekday() < dayofweek:
                    difference = dayofweek - x.isoweekday()
                    correctTime = correctTime + timedelta(days=difference)
                if x.isoweekday() > dayofweek:
                    difference = dayofweek - x.isoweekday() + 7
                    correctTime = correctTime + timedelta(days=difference)

            hourmatch = re.match('(?P<signal>(at|by)) (?P<hour>([0-9]{1,4}):?\s*([0-9]{2})?\s*)(?P<ampm>(am|pm|tonight|in the morning)?|noon|midnight)(\s|$)', answer, re.IGNORECASE)       
            if hourmatch is not None:
                    State = "Time"
                    Satisfied = True
                    timetype = "Hour"
                    parsehour = hourmatch.group('hour')
                    hour = hourmatch.group('hour')
                    timehint = hourmatch.group('ampm')
                    if timehint == "":
                        if int(hour) > 1259:
                            sethour = parsehour[0:2]
                            minutes = parsehour[2:4]
                            correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                        else:
                            if 2 < len(hour) < 4:
                                sethour = parsehour[0:1]
                                minutes = parsehour[1:3]
                                correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                            if len(hour) > 3:
                                sethour = parsehour[0:2]
                                minutes = parsehour[2:4]
                                correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                            if len(hour) == 1:
                                sethour = parsehour[0:1]
                                correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                            if len(hour) == 2:
                                print "yay"
                                sethour = parsehour[0:2]
                                correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                    if len(str(hour)) < 4:
                        for pmhints in pmWords:
                            if pmhints in timehint:
                                if int(hour) == 12:
                                    correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                                if int(hour) != 12:
                                    hour = int(hour) + 12
                                    correctTime = x.replace(hour=hour, minute=0, second=0, microsecond=0)
                        for amhints in amWords:
                            if amhints in timehint:
                                if int(hour) == 12:
                                    correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                                if int(hour) != 12:
                                    correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                    if len(str(hour)) > 3:
                        if len(str(hour)) == 4:
                            hour = parsehour[0]
                            minutes = parsehour[1:3]
                        if len(str(hour)) == 5:
                            hour = parsehour[0:2]
                            minutes = parsehour[2:4]
                        x = datetime.now(tz)
                        for pmhints in pmWords:
                            if pmhints in timehint:
                                if int(hour) == 12:
                                    correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                                if int(hour) != 12:
                                    hour = int(hour) + 12
                                    correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                        for amhints in amWords:
                            if amhints in timehint:
                                if int(hour) == 12:
                                    correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                                if int(hour) != 12:
                                    correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                    if hourmatch.group('signal') == "by":
                        correctTime = correctTime - timedelta(minutes=30)
                    if correctTime < x:
                        correctTime = correctTime + timedelta(days=1)

            locationmatch = re.match('(?P<location>When I ((?P<arrive>(get|arrive))|(?P<leave>(leave)))( to)?( at)? ((?P<default>home|work)|(?P<custom>[\S]+$)))', answer, re.IGNORECASE)
            if locationmatch is not None:
                State = "Time"
                Satisfied = True
                if locationmatch.group('arrive'):
                    timetype = ["Location", "Arrival"]
                if locationmatch.group('leave'):
                    timetype = ["Location", "Departure"]
                if locationmatch.group('default'):
                    locationToSearch = locationmatch.group('default')
                    locationToSearch = locationToSearch.capitalize()
                    correctTime = "_$!<{0}>!$_".format(locationToSearch)
                if locationmatch.group('custom'):
                    locationToSearch = locationmatch.group('custom')
                    correctTime = locationToSearch.capitalize()
                if timetype[1] == "Arrival":
                    ArriveDepart = "OnArrival"
                if timetype[1] == "Departure":
                    ArriveDepart = "OnDeparture"
                x = None

                if correctTime == "Here":
                    x = self.herefind()
                    identifier = None
                else:
                    x = locationFind(self, correctTime)
                    identifier = x[7]
                if x != None:
                    print x
                    Loc = Location()
                    Loc.street = x[2]
                    Loc.countryCode = x[6]
                    Loc.city = x[3]
                    Loc.label = correctTime
                    Loc.postalCode = x[4]
                    Loc.latitude = x[0]
                    Loc.stateCode = x[5]
                    Loc.longitude = x[1]
                    Loc.accuracy = "10.0"
                if x == None:
                    self.say("Sorry, I couldn't find that location in your contact card")
                    self.complete_request()
        
        if State == "noTime":
            self.say("Sorry, I didn't understand that...")        
        if timetype[0] == "Location":
            trig = ReminderLocationTrigger()
            trig.contactIdentifier = identifier
            trig.timing = ArriveDepart
            trig.location = Loc
        if timetype[0] is not "Location":
            trig = ReminderDateTimeTrigger()
            trig.timeZoneId = self.connection.assistant.timeZoneId
            trig.date = correctTime

        updateCMD = DomainObjectUpdate(self.refId)
        updateCMD.identifier = reminder       
        updateCMD.setFields = ReminderObject()
        updateCMD.setFields.trigger = trig
        updateCMD.setFields.important = False
        if timetype[0] is not "Location":
            updateCMD.setFields.dueDate = correctTime
            updateCMD.setFields.dueDateTimeZoneId = trig.timeZoneId
        updateCMD.setFields.completed = False

        
        
        answer = self.getResponseForRequest(updateCMD)
        if ObjectIsCommand(answer, DomainObjectUpdateCompleted):
            return reminder
        else:
            return None

    def showUpdatedReminderAndAskToCreate(self, reminder, language):
        createAnchor = self.createReminderSnippet(reminder, True, "Createreminder#updatedTime", random.choice(responses['showUpdatedReminder'][language]), language)
        
        response = self.getResponseForRequest(createAnchor)
        match = re.match("\^reminderConfirmation\^=\^(?P<answer>.*)\^", response)
        if match:
            response = match.group('answer')
        
        return response
    
    def cancelReminder(self, reminder, language):
        # cancel the reminder
        cancelCMD = DomainObjectCancel(self.refId)
        cancelCMD.identifier = ReminderObject()
        cancelCMD.identifier.identifier = reminder.identifier
        
        answer = self.getResponseForRequest(cancelCMD)
        if ObjectIsCommand(answer, DomainObjectCancelCompleted):
            createAnchor = UIAddViews(self.refId)
            createAnchor.dialogPhase = createAnchor.DialogPhaseCanceledValue
            cancelView = UIAssistantUtteranceView()
            cancelView.dialogIdentifier = "Createreminder#wontRemind"
            cancelView.text = cancelView.speakableText = random.choice(responses['cancelReminder'][language])
            createAnchor.views = [cancelView]
            
            self.sendRequestWithoutAnswer(createAnchor)
            self.complete_request()
        else:
            self.say(random.choice(responses['cancelFail'][language]))
            self.complete_request()
    
    def askForClarification(self, reminder, language):
        createAnchor = self.createReminderSnippet(reminder, True, "Createreminder#notReadyToRemind", random.choice(responses['clarification'][language]), language)
        
        response = self.getResponseForRequest(createAnchor)
        match = re.match("\^reminderConfirmation\^=\^(?P<answer>.*)\^", response)
        if match:
            response = match.group('answer')
            
        return response
        
    def reminding(self, content, correctTime, timetype, language, EndDate):
        ReminderObj = self.createNewReminder(content, correctTime, timetype, EndDate)
        if ReminderObj == None:
            self.say(random.choice(responses['updateReminderFailed'][language]))
            self.complete_request()
            return
        satisfied = False
        state = "SHOW"
        
        while not satisfied:
            ReminderObj = self.getReminderIdentifier(ReminderObj.identifier)
            if ReminderObj == None:
                self.say(u"Sorry I lost your reminder.")
                self.complete_request()
                return
            
            if state == "SHOW":
                instruction = self.showUpdatedReminderAndAskToCreate(ReminderObj, language).strip().lower()
                if any(k in instruction for k in (questions['answerCREATE'][language])):
                    state = "CREATE"
                    continue
                if any(k in instruction for k in (questions['answerCANCEL'][language])):
                    state = "CANCEL"
                    continue
                self.say(random.choice(responses['cantUnderstand'][language]))
                continue
            
            elif state == "CLARIFY":
                instruction = self.askForClarification(ReminderObj, language).strip().lower()
                if any(k in instruction for k in (questions['answerCREATE'][language])):
                    state = "CREATE"
                    continue
                if any(k in instruction for k in (questions['answerCANCEL'][language])):
                    state = "CANCEL"
                    continue
                self.say(random.choice(responses['cantUnderstand'][language]))
                continue
            
            elif state == "CANCEL":
                self.cancelReminder(ReminderObj, language)
                satisfied = True
                continue
            
            elif state == "CREATE":
                self.finalCommit(ReminderObj, language)
                satisfied = True
                continue
    def remindingnoinfo(self, content, language):
        ReminderObj = self.createnewremindernoinfo(content)
        if ReminderObj == None:
            self.say(random.choice(responses['updateReminderFailed'][language]))
            self.complete_request()
            return
        ReminderObj = self.askAndSetTime(ReminderObj, language)
        if ReminderObj == None:
            self.say(random.choice(responses['updateReminderFail'][language]))
            self.complete_request()
            return
        satisfied = False
        state = "SHOW"
        
        while not satisfied:
            ReminderObj = self.getReminderIdentifier(ReminderObj.identifier)
            if ReminderObj == None:
                self.say(u"Sorry I lost your reminder.")
                self.complete_request()
                return

            if state == "SHOW":
                instruction = self.showUpdatedReminderAndAskToCreate(ReminderObj, language).strip().lower()
                if any(k in instruction for k in (questions['answerCREATE'][language])):
                    state = "CREATE"
                    continue
                if any(k in instruction for k in (questions['answerCANCEL'][language])):
                    state = "CANCEL"
                    continue
                self.say(random.choice(responses['cantUnderstand'][language]))
                continue

            elif state == "CLARIFY":
                instruction = self.askForClarification(ReminderObj, language).strip().lower()
                if any(k in instruction for k in (questions['answerCREATE'][language])):
                    state = "CREATE"
                    continue
                if any(k in instruction for k in (questions['answerCANCEL'][language])):
                    state = "CANCEL"
                    continue
                self.say(random.choice(responses['cantUnderstand'][language]))
                continue

            elif state == "CANCEL":
                self.cancelReminder(ReminderObj, language)
                satisfied = True
                continue

            elif state == "CREATE":
                self.finalCommit(ReminderObj, language)
                satisfied = True
                continue
    
    @register("en-US", "(Create|Remind)( a)?( new)? (me|reminder) to (?P<content>[\w ]+?) ((?P<relative>(?P<relativeinteger>([0-9/ ])*|in||a|an|the)\s+(?P<relativeunits>(mins?|minutes?|hrs?|hours?|days?|weeks?)))|(?P<weekday>on (?P<dayofweek>(monday?|tuesday?|wednesday?|thursday?|friday?|saturday?|sunday?)) at ((?P<weekdayhour>([0-9]{1,2}):?\s*([0-9]{2})?\s*)(?P<weekdayampm>(am|pm))?|noon|midnight)(\s|$))|(?P<location>when I ((?P<arrive>(get|arrive))|(?P<leave>(leave)))( to)?( at)? ((?P<default>home|work)|(?P<custom>[\S]+$)))|(?P<hour>([0-9]{1,2}):?\s*([0-9]{2})?\s*)(?P<ampm>(am|pm|tonight|in the morning)?|noon|midnight))(\s|$)")
    def Remind(self, speech, lang, regex):
        ##print regex.groups()
        content = regex.group('content')
        conent = content.capitalize()
        tz = timezone(self.connection.assistant.timeZoneId)
        x = datetime.now(tz)
        EndDate = None
        pmWords = ["pm", "tonight"]
        amWords = ["am"]
        EndDate = None
        lastword = content.split()[-1] 
        if content != None:
            if regex.group('relative'):
                ##print "Using Relative"
                timetype = "Relative"
                relativeint = regex.group('relativeinteger')
                relativeunit = regex.group('relativeunits').strip("s").title()
                if relativeunit == "Minute":
                    z = int(relativeint) * 60
                    EndDate = x + timedelta(seconds=z)
                if relativeunit == "Hour":
                    z = int(relativeint) * 60 * 60
                    EndDate = x + timedelta(seconds=z)
                if relativeunit == "Day":
                    z = int(relativeint) * 24 * 60 * 60
                    EndDate = x + timedelta(seconds=z)
                if relativeunit == "Week":
                    z = int(relativeint) * 7 * 24 * 60 * 60
                    EndDate = x + timedelta(seconds=z)
                correctTime = z

            if regex.group('weekday'):
                ##print "Using Weekday"
                timetype = "Hour"
                dayofweek = regex.group('dayofweek')
                parsehour = regex.group('weekdayhour')
                hour = regex.group('weekdayhour')
                timehint = regex.group('weekdayampm')
                ##print timehint
                ##print hour
                if dayofweek == "monday":
                    dayofweek = 1
                if dayofweek == "tuesday":
                    dayofweek = 2
                if dayofweek == "wednesday":
                    dayofweek = 3
                if dayofweek == "thursday":
                    dayofweek = 4
                if dayofweek == "friday":
                    dayofweek = 5
                if dayofweek == "saturday":
                    dayofweek = 6
                if dayofweek == "sunday":
                    dayofweek = 7
                if timehint == "":
                    if int(hour) > 1259:
                        sethour = parsehour[0:2]
                        minutes = parsehour[2:4]
                        correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                    else:
                        if 2 < len(hour) < 4:
                            sethour = parsehour[0:1]
                            minutes = parsehour[1:3]
                            correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                        if len(hour) > 3:
                            sethour = parsehour[0:2]
                            minutes = parsehour[2:4]
                            correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                        if len(hour) == 1:
                            sethour = parsehour[0:1]
                            correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                        if len(hour) == 2:
                            sethour = parsehour[0:2]
                            correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                if len(str(hour)) < 4:
                    for pmhints in pmWords:
                        if pmhints in timehint:
                            ##print "using PM"
                            ##print hour
                            if int(hour) == 12:
                                correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                            if int(hour) != 12:
                                hour = int(hour) + 12
                                correctTime = x.replace(hour=hour, minute=0, second=0, microsecond=0)
                    for amhints in amWords:
                        if amhints in timehint:
                            ##print "using AM"
                            if int(hour) == 12:
                                correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                            if int(hour) != 12:
                                correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                if len(str(hour)) > 3:
                    if len(str(hour)) == 4:
                        hour = parsehour[0]
                        minutes = parsehour[1:3]
                    if len(str(hour)) == 5:
                        hour = parsehour[0:2]
                        minutes = parsehour[2:4]
                    ##print hour
                    ##print minutes
                    x = datetime.now(tz)
                    for pmhints in pmWords:
                        if pmhints in timehint:
                            ##print "using PM"
                            if int(hour) == 12:
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                            if int(hour) != 12:
                                hour = int(hour) + 12
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                    for amhints in amWords:
                        if amhints in timehint:
                            ##print "using AM"
                            if int(hour) == 12:
                                correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                            if int(hour) != 12:
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                ##print x.isoweekday()
                ##print dayofweek
                if x.isoweekday() < dayofweek:
                    difference = dayofweek - x.isoweekday()
                    correctTime = correctTime + timedelta(days=difference)
                if x.isoweekday() > dayofweek:
                    difference = dayofweek - x.isoweekday() + 7
                    correctTime = correctTime + timedelta(days=difference)
            if regex.group('location'):
                print "Using Location"
                if regex.group('arrive'):
                    timetype = ["Location", "Arrival"]
                if regex.group('leave'):
                    timetype = ["Location", "Departure"]
                if regex.group('default'):
                    locationToSearch = regex.group('default')
                    locationToSearch = locationToSearch.capitalize()
                    correctTime = "_$!<{0}>!$_".format(locationToSearch)
                if regex.group('custom'):
                    locationToSearch = regex.group('custom')
                    correctTime = locationToSearch.capitalize()
            if regex.group('hour'):
                timetype = "Hour"
                parsehour = regex.group('hour')
                hour = regex.group('hour')
                timehint = regex.group('ampm')
                if timehint == "":
                    if int(hour) > 1259:
                        sethour = parsehour[0:2]
                        minutes = parsehour[2:4]
                        correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                    else:
                        if 2 < len(hour) < 4:
                            sethour = parsehour[0:1]
                            minutes = parsehour[1:3]
                            correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                        if len(hour) > 3:
                            sethour = parsehour[0:2]
                            minutes = parsehour[2:4]
                            correctTime = x.replace(hour=int(sethour), minute=int(minutes), second=0, microsecond=0)
                        if len(hour) == 1:
                            sethour = parsehour[0:1]
                            correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                        if len(hour) == 2:
                            print "yay"
                            sethour = parsehour[0:2]
                            correctTime = x.replace(hour=int(sethour), minute=0, second=0, microsecond=0)
                if len(str(hour)) < 4:
                    for pmhints in pmWords:
                        if pmhints in timehint:
                            ##print "using PM"
                            ##print hour
                            if int(hour) == 12:
                                correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                            if int(hour) != 12:
                                hour = int(hour) + 12
                                correctTime = x.replace(hour=hour, minute=0, second=0, microsecond=0)
                    for amhints in amWords:
                        if amhints in timehint:
                            ##print "using AM"
                            if int(hour) == 12:
                                correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                            if int(hour) != 12:
                                correctTime = x.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                if len(str(hour)) > 3:
                    if len(str(hour)) == 4:
                        hour = parsehour[0]
                        minutes = parsehour[1:3]
                    if len(str(hour)) == 5:
                        hour = parsehour[0:2]
                        minutes = parsehour[2:4]
                    x = datetime.now(tz)
                    for pmhints in pmWords:
                        if pmhints in timehint:
                            ##print "using PM"
                            if int(hour) == 12:
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                            if int(hour) != 12:
                                hour = int(hour) + 12
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                    for amhints in amWords:
                        if amhints in timehint:
                            ##print "using AM"
                            if int(hour) == 12:
                                correctTime = x.replace(hour=23, minute=59, second=0, microsecond=0)
                            if int(hour) != 12:
                                correctTime = x.replace(hour=int(hour), minute=int(minutes), second=0, microsecond=0)
                if lastword == "by":
                    correctTime = correctTime - timedelta(minutes=30)
                if correctTime < x:
                    correctTime = correctTime + timedelta(days=1)

            if lastword == "at":
                content = content.replace(" at", "")
            if lastword == "in":
                content = content.replace(" in", "")
            if lastword == "by":
                content = content.replace(" by", "")
            self.reminding(content, correctTime, timetype, lang, EndDate)                             
        self.complete_request()
        
    @register("en-US", "(Create|Remind)( a)?( new)? (me|reminder) to (?P<content>[\w ]+?)$")
    def RemindNoInfo(self, speech, lang, regex):
        content = regex.group('content')
        content = content.capitalize()
        if content != None:
            self.remindingnoinfo(content, lang)
            return
        self.say(responses['notFound'][lang])                         
        self.complete_request()