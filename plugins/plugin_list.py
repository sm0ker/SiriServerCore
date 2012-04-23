#!/usr/bin/python
# -*- coding: utf-8 -*-

import re,os

config_file="plugins.conf"
pluginPath="plugins"
from plugin import *
tline_answer_de = ''
tline_answer_en = ''

with open(config_file, "r") as fh:
    for line in fh:
        line = line.strip()
        if line.startswith("#") == 0 :
            tline_answer_en = tline_answer_en +'\n' + "".join(line)

class help(Plugin):

    @register("de-DE", "(Script)|(Scripts)")
    @register("en-US", "(Plugin)|(Plugins)")
    def st_hello(self, speech, language):
        if language == 'de-DE':
            self.say("Hier werden die Plugins in Ihrem Server installiert:")
            self.say(tline_answer_de ,' ')
        else:
            self.say("Here are the plugins installed in your server:")
            self.say(tline_answer_en ,' ')
        self.complete_request()

