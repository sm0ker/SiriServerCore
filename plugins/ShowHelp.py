#!/usr/bin/env python
# encoding: utf-8
"""
ShowHelp plugin for SiriServerCore
Created by Javik

"""

from siriObjects.uiObjects import UIShowHelp
from plugin import *



class ShowHelp(Plugin):
	@register("en-US","What can you do")
	def st_show_help(self, speech, language):
		if language == 'en-US':
			help = UIShowHelp(self.refId)
			help.speakableText = "You can ask things like:"
			help.text = "You can ask things like:"
			answer = self.getResponseForRequest(help)
			self.complete_request()
