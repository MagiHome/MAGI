﻿README for Linux SDK
-----------------------

bin：
|-- msc
    |-- msc.cfg（作用：msc调试、生成msc日志）
|-- wav（符合标准的音频文件样例）
|-- 示例程序可执行文件（samples目录下对应示例生成的可执行文件，编译sample源码后生成）
|-- gm_continuous_digit.abnf（abnf语法样例）
|-- userwords.txt（用户词表样例）

doc：
|-- iFlytek MSC Reference Manual（API文档，HTML格式）
|-- MSC Novice Manual for Linux.pdf（MSC新手指南）
|-- Grammar Development Guidelines（语音识别语法规范）
|-- Open Semantic Platform API Documents（语义开放平台API文档）

include：调用SDK所需头文件

libs：
|-- x86
	|-- libmsc.so（32位动态库）
|-- x64
	|-- libmsc.so（64位动态库）
|--Raspberry Pi
	|-- libmsc.so（32位动态库）
|-- arm
	|-- readme.txt（获取相应平台SDK的方法）
|--mips
	|-- readme.txt（获取相应平台SDK的方法）

samples：
|-- asr_sample（语音识别示例）
	|-- asr_sample.c
	|-- Makefile
	|-- make.sh（分为32位和64位执行脚本，建议执行命令：source make.sh，shell脚本会自动设置SDK搜索路径，可根据实际需要修改。）
|-- iat_sample（语音听写示例）
	|-- iat_sample.c
	|-- Makefile
	|-- make.sh
|-- tts_sample（语音合成示例）
	|-- tts_sample.c
	|-- Makefile
	|-- make.sh