import os
import shutil
import glob
newest = max(glob.iglob('/config/tts/tts.wav'), key=os.path.getctime)
shutil.copy(newest, '/config/tts/play.wav')
os.remove(newest)
