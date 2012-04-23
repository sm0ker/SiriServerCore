#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib2, urllib
import json
import logging
from uuid import uuid4
from plugin import *

from siriObjects.baseObjects import AceObject, ClientBoundCommand
from siriObjects.uiObjects import AddViews, AssistantUtteranceView
from siriObjects.systemObjects import DomainObject, DomainObjectCreate, DomainObjectRetrieve, DomainObjectUpdate, DomainObjectCommit
from siriObjects.reminderObjects import *

class Create(ClientBoundCommand):
    def __init__(self, refId=None, important=False, completed=False, subject=""):
        super(Create, self).__init__("Object", "com.apple.ace.reminder", None, None)
        self.subject = subject
        self.important = False
        self.completed = False
        
    def to_plist(self):
    	self.add_item('important')
        self.add_item('completed')
        self.add_property('subject')
        return super(Create, self).to_plist()

class Update(ClientBoundCommand):
    def __init__(self, refId=None, identifier=""):
        super(Update, self).__init__("Reminder", "com.apple.ace.reminder", None, None)
        self.identifier = identifier

    def to_plist(self):
        self.add_property('identifier')
        return super(Update, self).to_plist()

class reminders(Plugin):
    localizations = {"reminderDefaults": 
                        {"searching":{"en-US": "Creating your reminder ..."}, 
                         "result": {"en-US": "Here is your reminder:"},
                         "nothing": {"en-US": "What should I remind you of?"}}, 
                    "failure": {
                                "en-US": "I cannot create your reminder right now."
                                }
                    }
    @register("en-US", "(.*remind [a-zA-Z0-9]+)|(.*create.*reminder [a-zA-Z0-9]+)|(.*set.*reminder [a-zA-Z0-9]+)")
    def createReminder(self, speech, language):
        content_raw = re.match(".*reminder ([a-zA-Z0-9, ]+)$", speech, re.IGNORECASE)
        if content_raw == None:
            view_initial = AddViews(self.refId, dialogPhase="Reflection")
            view_initial.views = [AssistantUtteranceView(text=reminders.localizations['reminderDefaults']['nothing'][language], speakableText=reminders.localizations['reminderDefaults']['nothing'][language], dialogIdentifier="Reminder#failed")]
            self.sendRequestWithoutAnswer(view_initial)
        else:
            view_initial = AddViews(self.refId, dialogPhase="Reflection")
            view_initial.views = [AssistantUtteranceView(text=reminders.localizations['reminderDefaults']['searching'][language], speakableText=reminders.localizations['reminderDefaults']['searching'][language], dialogIdentifier="Reminder#creating")]
            self.sendRequestWithoutAnswer(view_initial)
            
            content_raw = content_raw.group(1).strip()
            if "me to" in content_raw:
                split = content_raw.split(' ')
                if split[0] == "me to":
                    split.pop(0)
                    content_raw = ' '.join(map(str, split))
            if "for" in content_raw:
                split = content_raw.split(' ')
                if split[0] == "for":
                    split.pop(0)
                    content_raw = ' '.join(map(str, split))

			# adds reminder
            reminder_create = Create()
            reminder_create.subject = content_raw
            domain_object = DomainObjectCreate(refId = self.refId)
            domain_object.object = reminder_create
            reminder_return = self.getResponseForRequest(domain_object)
            print reminder_return

			# retrieves reminder
			
			# update / commit reminder
            reminder_update = Update()
            reminder_update.identifier = reminder_return["properties"]["identifier"]
            domain_object_up = DomainObjectCommit(refId = self.refId)
            domain_object_up.identifier = reminder_update
            reminder_update_return = self.getResponseForRequest(domain_object_up)
            print reminder_update_return
			# send view
        
            view = AddViews(self.refId, dialogPhase="Summary")
            view1 = AssistantUtteranceView(text=reminders.localizations['reminderDefaults']['result'][language], speakableText=reminders.localizations['reminderDefaults']['result'][language], dialogIdentifier="Reminder#created")
        
            reminder_ = ReminderObject()
            reminder_.subject = content_raw
            reminder_.identifier = reminder_return["properties"]["identifier"]
        
            view2 = ReminderSnippet(reminders=[reminder_])
            view.views = [view1, view2]
            self.sendRequestWithoutAnswer(view)
        self.complete_request()
