from app.core import Core

fut = Core('slats1999@gmail.com', '$Logan1992')

while(True):
    try:
        fut.bronzePackMethod()
    except:
        print('exception')
        break
        #clear unused