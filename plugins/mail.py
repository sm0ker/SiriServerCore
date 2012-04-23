#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
---------------------------------------------------------------------
Authors :
Created by Daniel Zaťovič (P4r4doX)
Contacts search code is taken from phonecalls plugin by Eichhoernchen
Special thanks to doratown for providing original plists from 4S
---------------------------------------------------------------------
About :
Using this plugin you can write email directly from Siri
---------------------------------------------------------------------
Usage :
Email <name> about <subject>
---------------------------------------------------------------------
Todo :
Check email
---------------------------------------------------------------------
Instalation :
Just create folder called email in your plugins directory, and place 
this file into it. Then add "mail" to your plugins.conf
---------------------------------------------------------------------
IMPORTANT :
You MUST download the newest version of SiriServerCore. becouse 
Eichhoernchen have changed some objects to work with this plugin.
---------------------------------------------------------------------
Changelog :
v1.0 (19th March 2012) - initial Alpha release
"""


from plugin import *
from siriObjects.baseObjects import *
from siriObjects.uiObjects import *
from siriObjects.emailObjects import *
from siriObjects.systemObjects import *
from siriObjects.contactObjects import PersonSearch, PersonSearchCompleted
from plugin import *
from siriObjects.phoneObjects import PhoneCall
import re
import time

responses = {
'notFound': 
    {'de-DE': u"Entschuldigung, ich konnte niemanden in deinem Telefonbuch finden der so heißt",
     'en-US': u"Sorry, I did not find a match in your phone book"
    },
'devel':
    {'de-DE': u"Entschuldigung, aber diese Funktion befindet sich noch in der Entwicklungsphase",
     'en-US': u"Sorry this feature is still under development"
    },
'select':
    {'de-DE': u"Wen genau?", 
     'en-US': u"Which one?"
    },
'selectNumber':
    {'de-DE': u"Welche Email Adresse für {0}",
     'en-US': u"Which email adress one for {0}"
    }
}

numberTypesLocalized= {
'_$!<Mobile>!$_': {'en-US': u"mobile", 'de-DE': u"Handynummer"},
'iPhone': {'en-US': u"iPhone", 'de-DE': u"iPhone-Nummer"},
'_$!<Home>!$_': {'en-US': u"home", 'de-DE': u"Privatnummer"},
'_$!<Work>!$_': {'en-US': u"work", 'de-DE': u"Geschäftsnummer"},
'_$!<Main>!$_': {'en-US': u"main", 'de-DE': u"Hauptnummer"},
'_$!<HomeFAX>!$_': {'en-US': u"home fax", 'de-DE': u'private Faxnummer'},
'_$!<WorkFAX>!$_': {'en-US': u"work fax", 'de-DE': u"geschäftliche Faxnummer"},
'_$!<OtherFAX>!$_': {'en-US': u"_$!<OtherFAX>!$_", 'de-DE': u"_$!<OtherFAX>!$_"},
'_$!<Pager>!$_': {'en-US': u"pager", 'de-DE': u"Pagernummer"},
'_$!<Other>!$_':{'en-US': u"other phone", 'de-DE': u"anderes Telefon"}
}

namesToNumberTypes = {
'de-DE': {'mobile': "_$!<Mobile>!$_", 'handy': "_$!<Mobile>!$_", 'zuhause': "_$!<Home>!$_", 'privat': "_$!<Home>!$_", 'arbeit': "_$!<Work>!$_"},
'en-US': {'work': "_$!<Work>!$_",'home': "_$!<Home>!$_", 'mobile': "_$!<Mobile>!$_"}
}

speakableDemitter={
'en-US': u", or ",
'de-DE': u', oder '}

errorNumberTypes= {
'de-DE': u"Ich habe dich nicht verstanden, versuch es bitte noch einmal.",
'en-US': u"Sorry, I did not understand, please try again."
}

errorNumberNotPresent= {
'de-DE': u"Ich habe diese {0} von {1} nicht, aber eine andere.",
'en-US': u"Sorry, I don't have a {0} email from {1}, but another."
}

class mail(Plugin):
  
    def searchUserByName(self, personToLookup):
        search = PersonSearch(self.refId)
        search.scope = PersonSearch.ScopeLocalValue
        search.name = personToLookup
        answerObj = self.getResponseForRequest(search)
        if ObjectIsCommand(answerObj, PersonSearchCompleted):
            answer = PersonSearchCompleted(answerObj)
            return answer.results if answer.results != None else []
        else:
            raise StopPluginExecution("Unknown response: {0}".format(answerObj))
        return []
           
    def getNumberTypeForName(self, name, language):
        # q&d
        if name != None:
            if name.lower() in namesToNumberTypes[language]:
                return namesToNumberTypes[language][name.lower()]
            else:
                for key in numberTypesLocalized.keys():
                    if numberTypesLocalized[key][language].lower() == name.lower():
                        return numberTypesLocalized[key][language]
        return None
    
    def findPhoneForNumberType(self, person, numberType, language):         
        # first check if a specific number was already requested
        phoneToCall = None
        if numberType != None:
            # try to find the phone that fits the numberType
            phoneToCall = filter(lambda x: x.label == numberType, person.emails)
        else:
            favPhones = filter(lambda y: y.favoriteVoice if hasattr(y, "favoriteVoice") else False, person.emails)
            if len(favPhones) == 1:
                phoneToCall = favPhones[0]
        if phoneToCall == None:
            # lets check if there is more than one number
            if len(person.emails) == 1:
                if numberType != None:
                    self.say(errorNumberNotPresent.format(numberTypesLocalized[numberType][language], person.fullName))
                phoneToCall = person.emails[0]
            else:
                # damn we need to ask the user which one he wants...
                while(phoneToCall == None):
                    rootView = AddViews(self.refId, temporary=False, dialogPhase="Clarification", scrollToTop=False, views=[])
                    sayit = responses['selectNumber'][language].format(person.fullName)
                    rootView.views.append(AssistantUtteranceView(text=sayit, speakableText=sayit, listenAfterSpeaking=True,dialogIdentifier="ContactDataResolutionDucs#foundAmbiguousPhoneNumberForContact"))
                    lst = DisambiguationList(items=[], speakableSelectionResponse="OK...", listenAfterSpeaking=True, speakableText="", speakableFinalDemitter=speakableDemitter[language], speakableDemitter=", ",selectionResponse="OK...")
                    rootView.views.append(lst)
                    for phone in person.emails:
                        numberType = phone.label
                        item = ListItem()
                        item.title = ""
                        item.text = u"{0}: {1}".format(numberTypesLocalized[numberType][language], phone.emailAddress)
                        item.selectionText = item.text
                        item.speakableText = u"{0}  ".format(numberTypesLocalized[numberType][language])
                        item.object = phone
                        item.commands.append(SendCommands(commands=[StartRequest(handsFree=False, utterance=numberTypesLocalized[numberType][language])]))
                        lst.items.append(item)
                    answer = self.getResponseForRequest(rootView)
                    numberType = self.getNumberTypeForName(answer, language)
                    if numberType != None:
                        matches = filter(lambda x: x.label == numberType, person.emails)
                        if len(matches) == 1:
                            phoneToCall = matches[0]
                        else:
                            self.say(errorNumberTypes[language])
                    else:
                        self.say(errorNumberTypes[language])
        return phoneToCall

    def presentPossibleUsers(self, persons, language):
        root = AddViews(self.refId, False, False, "Clarification", [], [])
        root.views.append(AssistantUtteranceView(responses['select'][language], responses['select'][language], "ContactDataResolutionDucs#disambiguateContact", True))
        lst = DisambiguationList([], "OK!", True, "OK!", speakableDemitter[language], ", ", "OK!")
        root.views.append(lst)
        for person in persons:
            item = ListItem(person.fullName, person.fullName, [], person.fullName, person)
            item.commands.append(SendCommands([StartRequest(False, "^phoneCallContactId^=^urn:ace:{0}".format(person.identifier))]))
            lst.items.append(item)
        return root       

    @register("en-US", "(email)* ([\w ]+) *about* ([\w ]+)")  
    def mail(self, speech, language, regex):
	personToCall = regex.group(2)
	subject = regex.group(3)
        numberType = ""
        numberType = self.getNumberTypeForName(numberType, language)
        persons = self.searchUserByName(personToCall)
        personToCall = None
        if len(persons) > 0:
            if len(persons) == 1:
                personToCall = persons[0]
            else:
                identifierRegex = re.compile("\^phoneCallContactId\^=\^urn:ace:(?P<identifier>.*)")
                #  multiple users, ask user to select
                while(personToCall == None):
                    strUserToCall = self.getResponseForRequest(self.presentPossibleUsers(persons, language))
                    self.logger.debug(strUserToCall)
                    # maybe the user clicked...
                    identifier = identifierRegex.match(strUserToCall)
                    if identifier:
                        strUserToCall = identifier.group('identifier')
                        self.logger.debug(strUserToCall)
                    for person in persons:
                        if person.fullName == strUserToCall or person.identifier == strUserToCall:
                            personToCall = person
                    if personToCall == None:
                        # we obviously did not understand him.. but probably he refined his request... call again...
                        self.say(errorNumberTypes[language])
                    
            if personToCall != None:
		personAttribute=PersonAttribute()
		targetEmailAdress = self.findPhoneForNumberType(personToCall, numberType, language)
		personAttribute.data = targetEmailAdress.emailAddress
		personAttribute.displayText = personToCall.fullName
		PersonObject = Person()
		PersonObject.identifier = personToCall.identifier
		personAttribute.object=PersonObject
		self.say("Creating email ...", " ")
		email = EmailEmail()
		email.subject = subject.title()
		email.recipientsTo = [personAttribute]
		email.outgoing = True
		email.type = "New"
		EmailDomain = DomainObjectCreate(self.refId, email)
		answer = self.getResponseForRequest(EmailDomain)
		
		if ObjectIsCommand(answer, DomainObjectCreateCompleted):
		      identifier = DomainObjectCreateCompleted(answer)
		      self.logger.debug("DomainObject identifier : {0}".format(identifier.identifier))
		      DomainIdentifier = identifier.identifier
		else:
		      raise StopPluginExecution("Unknown response: {0}".format(answer))
		email.identifier = DomainIdentifier
		EmailView = AddViews(self.refId, dialogPhase="Clarification")
		
		Ask = AssistantUtteranceView("What you want to tell {0}".format(personToCall.firstName), "What you want to tell {0}".format(personToCall.firstName), listenAfterSpeaking=True)
		
		MyEmailSnippet = 0
		MyEmailSnippet = EmailSnippet()
		MyEmailSnippet.emails = [email]
		EmailView.views = [Ask, MyEmailSnippet]
		EmailView.scrollToTop = True
		print "Sending view ..."
		messageFU = self.getResponseForRequest(EmailView)
		print messageFU
		
		
		DomainUpdate = DomainObjectUpdate(self.refId)
		
		UpdateField = EmailEmail()
		UpdateField.message = messageFU
		DomainUpdate.setFields = UpdateField
		
		DomainUpdate.addFields = EmailEmail()
		
		UpdateDomainIdentifier = EmailEmail()
		UpdateDomainIdentifier.identifier = DomainIdentifier
		DomainUpdate.identifier = UpdateDomainIdentifier
		time.sleep(2)
		print "Sending update request ..."
		DomainUpdateAnswer = self.getResponseForRequest(DomainUpdate)
		
		if ObjectIsCommand(DomainUpdateAnswer, DomainObjectUpdateCompleted):
		      print "Recived DomainObjectUpdateCompleted !"
		else:
		      raise StopPluginExecution("Unknown response: {0}".format(answer))
		
		DomainRetrieve = DomainObjectRetrieve(self.refId)
		DomainObjectRetrieve.identifiers=[DomainIdentifier]
		print "Sending Retrieve object ..."
		DomainRetrieveAnswer = self.getResponseForRequest(DomainRetrieve)
		
		if ObjectIsCommand(DomainRetrieveAnswer, DomainObjectRetrieveCompleted):
		      print "Recived DomainObjectRetrieveCompleted !"
		else:
		      raise StopPluginExecution("Unknown response: {0}".format(answer))		
		
		FinallAsk = AssistantUtteranceView("Ready to send ?", "Ready to send ?", listenAfterSpeaking=True)
		
		FinallEmail = EmailEmail()
		FinallEmail.identifier = DomainIdentifier
		
		FinallSnippet = EmailSnippet()
		FinallSnippet.emails = [FinallEmail]
		
		FinallView = AddViews(self.refId, dialogPhase="Clarification")
		FinallView.views = [FinallAsk, FinallSnippet]
		FinallView.scrollToTop = True
		
		ReadyToSend = self.getResponseForRequest(FinallView)
		
		if(ReadyToSend == "Yes"):
		  CommitEmail = EmailEmail()
		  CommitEmail.identifier = DomainIdentifier
		  
		  Commit = DomainObjectCommit(self.refId)
		  Commit.identifier = CommitEmail
		  
		  CommitAnswer = self.getResponseForRequest(Commit)
		  print "Recived answer !"
		  if ObjectIsCommand(CommitAnswer, DomainObjectCommitCompleted):
		      print "Recived DomainObjectCommitCompleted !"      
		      self.say("I sent it !")
		  else:
		      raise StopPluginExecution("Unknown response: {0}".format(answer))
		else:
		  self.say("OK, I'll forget it !")		
		self.complete_request()                
        
        self.say(responses['notFound'][language])                         
        self.complete_request()


      
      
      
      
      
      
      
      
