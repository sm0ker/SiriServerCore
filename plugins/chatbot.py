from plugin import *
import urllib2 
from xml.dom.minidom import parseString

botID= "c8c7a9e2be344a53"

def askBOT(input):	
	#convert symbols to HEX
	input = input.replace(' ', '%20')
	input = input.replace('?', '%3F')
	input = input.replace('$', '%24')
	input = input.replace('+', '%2B')
	input = input.replace(',', '%2C')
	input = input.replace('/', '%2F')
	input = input.replace(':', '%3A') 
	input = input.replace(';', '%3B') 
	input = input.replace('=', '%3D') 
	input = input.replace('@', '%40')      
	file = urllib2.urlopen('http://www.pandorabots.com/pandora/talk-xml?botid=%s&input=%s' % (botID, input))	
	data = file.read()	
	file.close()	
	dom = parseString(data) 
	xmlTag = dom.getElementsByTagName('that')[0].toxml()	
	xmlData=xmlTag.replace('<that>','').replace('</that>','')
	#xmlData = xmlData.replace('Eve', 'Siri')
	#convert symbols
	xmlData = xmlData.replace('&quot;', '"')
	xmlData = xmlData.replace('&lt;', '<')
	xmlData = xmlData.replace('&gt;', '>')
	xmlData = xmlData.replace('&amp;', '&')
	xmlData = xmlData.replace('<br>', ' ')
	xmlData = xmlData.replace('I was created by ', 'I was created by Apple')
	xmlData = xmlData.replace('Ashanti', 'Siri')
	xmlData = xmlData.replace('Clownfish', 'Siri')
	xmlData = xmlData.replace('Shark Labs', 'Apple')
	xmlData = xmlData.replace('My is Raven', 'I was made by Apple')
	xmlData = xmlData.replace('I obey Raven', 'I was made by Apple in California')
	return xmlData


class chatBOT(Plugin):

    @register("en-US", ".*")
    def BOT_Message(self, speech, language):
	if language == 'en-US':     
	    self.say(askBOT(speech))
	    self.complete_request()

   
