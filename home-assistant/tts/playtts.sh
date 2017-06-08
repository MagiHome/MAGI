#!/bin/bash
export TTS_HOME="/usr/src/app/tts"
export TTS_CACHE="/config/tts"
export LD_LIBRARY_PATH=$TTS_HOME
$TTS_HOME/tts $1
python $TTS_HOME/play.py
cvlc file:///$TTS_CACHE/play.wav vlc://quit
