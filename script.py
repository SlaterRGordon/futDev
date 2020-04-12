from core import Core
from datetime import datetime
import time

while(True):
    timeStart = datetime.now()
    fut = Core('slats1999@gmail.com', '$Logan1992')
    fut.clubToSbc()
    while((datetime.now() - timeStart).seconds < 3600):
        fut.bronzePackMethod()
    fut.logout()
    time.sleep(3600)

    
