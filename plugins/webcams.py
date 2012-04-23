
from plugin import *
from plugin import __criteria_key__

from siriObjects.uiObjects import AddViews
from siriObjects.answerObjects import AnswerSnippet, AnswerObject, AnswerObjectLine

class webcams(Plugin):
    
    @register("en-US", "(How does it look in).*([\w ]+)")
    def webcam(self, speech, language):
        URL = ''
	
        Title = speech.replace ('How does it look in ', '')

        print Title
        if Title == "austin":
            URL = u'http://12.52.91.101/jpg/image.jpg'
        elif Title == "yosemite":
            URL = u'http://maps.ca.water.usgs.gov/webcams/happyisles-latest.jpg'
        elif Title == "fort collins":
            URL = u'http://www.co.larimer.co.us/webcam/old_courthouse.jpg'
        elif Title == "boulder":
            URL = u'http://www.esrl.noaa.gov/gsd/webcam/flatiron.jpg'
        elif Title == "san francisco":
            URL = u'http://hd-sf.com/images/livedata/480-live.jpg'
        elif Title == "lake travis":
            URL = u'http://media.lintvnews.com/BTI/KXAN02.jpg'
       
			
			
			
			
       
        view = AddViews(self.refId, dialogPhase="Completion")
        ImageAnswer = AnswerObject(title=str(Title),lines=[AnswerObjectLine(image=URL)])
        view1 = AnswerSnippet(answers=[ImageAnswer])
        view.views = [view1]
        self.sendRequestWithoutAnswer(view)
        self.complete_request()
        
           
