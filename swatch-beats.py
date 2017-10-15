from __future__ import print_function
import time

def beats():
        t=time.gmtime()
        h, m, s=t.tm_hour, t.tm_min, t.tm_sec

        utc=3600*h+60*m+s # UTC

        bmt=utc+3600 # Biel Mean Time (BMT)

        beat=bmt/86.4

        if beat>1000:
                beat-=1000

        return beat

def swatch():
        return "@%06.2f" % (beats())

if __name__=="__main__":
        print(swatch())
