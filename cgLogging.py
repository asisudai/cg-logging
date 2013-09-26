#!/bin/env python
# Copyright (c) 2013, Asi Soudai - www.asimation.com
# All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#

"""
Wrapper above built-in python logging module to help logging to Shell, Maya and Nuke
directly using timestamp and logging-level to keep the logs clean.

Also, both Maya and Nuke have specific handlers that allow application sepcific logging
using warning and popup messages that are native to those applications.
fatal and critical levels will pop a warning message in Nuke and Maya to make sure
user attention was grabbed when needed.

To use:
    log = getLogger( 'mylogger' )
    log.info( 'log something' )

    # Set level to debug
    log = getLogger( 'mylogger', level=DEBUG )
    # OR
    log = getLogger( 'mylogger' )
    log.setLevel( DEBUG )

    # Alart user:
    try:
        ... do something
    except Exception, error :
        log.fatal( "pop up this message if we're in nuke or maya" )
        raise error # re raise the error after we msg the user.
"""

## -----------------------------------------------------------------------------
# Imports
## -----------------------------------------------------------------------------
import sys
import logging

## Inside Maya?
try:
    import maya
    _in_maya = True
except Exception:
    _in_maya = False

## Inside Nuke?
try:
    import nuke
    _in_nuke = True
except Exception:
    _in_nuke = False


## -----------------------------------------------------------------------------
# Globals
## -----------------------------------------------------------------------------
MSG_FORMAT  = "%(asctime)s %(name)s %(levelname)s : %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# Levels
CRITICAL = 50
FATAL    = CRITICAL
ERROR    = 40
WARNING  = 30
WARN     = WARNING
INFO     = 20
DEBUG    = 10
NOTSET   = 0



## -----------------------------------------------------------------------------
# getLogger - Main call to grab a logger instance
## -----------------------------------------------------------------------------
def getLogger( name, shell=True, maya=_in_maya, nuke=_in_nuke, file=None, level=INFO ):
    '''
    Get logger - mimicing logging.getLogger() usage.

        name(str)  : logger name
        shell(bol) : output to shell/stdout
        maya(bol)  : output to maya script editor
        nuke(bol)  : output to nuke script editor
        file(str)  : output log into given fullpath-filename
        level(int) : logger level. default to INFO

    Example:
        log = getLogger( 'mylogger' )
        log.info( 'log something' )
    '''
    return Logger( name, shell, maya, nuke, file, level )


## -----------------------------------------------------------------------------
# Logger Class
## -----------------------------------------------------------------------------
class Logger(object):

    def __init__( self, name, shell=True, maya=False, nuke=False, file=None, level=INFO ):

        self._name = name
        self._log  = logging.getLogger(name)
        self._log.setLevel( level )

        ## SafetyCheck - since logging.getLogger support multi threads, if logger
        ##               was already created, it should also have the handlers too.
        ##               so let's avoid creating handlers again, so we won't get
        ##               double handlers... and make a double eveything.
        if self._log.handlers:
            # Logger already have handlers, no need to add more.
            return

        # Format
        format  = logging.Formatter( MSG_FORMAT, DATE_FORMAT )

        # Shell:
        if shell:
            stream_hdlr = ShellHandler()
            stream_hdlr.setFormatter( format )
            self._log.addHandler( stream_hdlr )

        # File:
        if file:
            file_hdlr = logging.FileHandler(file)
            file_hdlr.setFormatter( format )
            self._log.addHandler( file_hdlr )

        # Maya:
        if maya and _in_maya:
            maya_hdlr = MayaHandler()
            maya_hdlr.setFormatter( format )
            self._log.addHandler( maya_hdlr )

        # Nuke:
        if nuke and _in_nuke:
            nuke_hdlr = NukeHandler()
            nuke_hdlr.setFormatter( format )
            self._log.addHandler( nuke_hdlr )

    def __getattr__(self, attr):
        '''
        expose builtin logger attributes.
        this won't be needed if I could inherit the logger directly.
        But the logging.getLoggerClass() don't seem to work without jumping
        through to many hoops to make it worth it.
        '''
        if hasattr( self._log, attr ):
            return getattr( self._log, attr )
        else:
            raise AttributeError, "No attribute %s" %attr

    def __repr__(self):
        return "%s(%s Level:%i)" % ( self.__class__, self._name, self.level )



    ## LEVELS
    def debug(self, msg):
        self._log.debug(msg)

    def info(self, msg):
        self._log.info(msg)

    def warning(self, msg):
        self._log.warning(msg)

    def error(self, msg):
        self._log.error(msg)

    def fatal(self, msg):
        self._log.fatal(msg)

    def critical(self, msg):
        self._log.critical(msg)


## -----------------------------------------------------------------------------
# ShellHandler
## -----------------------------------------------------------------------------
class ShellHandler(logging.Handler):
    '''
    Shell Handler - emits logs to stdout.
    we'll use sys.__stdout__ to bypass maya and nuke script-editors
    so they won't show double logging.
    '''

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        sys.__stdout__.write( "%s\n" %self.format(record) )


## -----------------------------------------------------------------------------
# MayaHandler
## -----------------------------------------------------------------------------
class MayaHandler(logging.Handler):
    '''
    Maya specific handler - will emit warnings using nuke.warning()
    and critical and fatal levels will popup a warning dialog so artists
    won't miss important errors.
    '''
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):

        # Formated message:
        msg = self.format(record)

        if record.funcName == "warning":
            maya.cmds.warning( "\n"+msg )

        elif record.funcName in [ "critical", "fatal" ]:

            ## Emit stdout print:
            sys.stdout.write("\n"+msg+"\n")

            ## Open dialog if not in batch mode:
            if maya.cmds.about( batch=True ) == False:

                maya.cmds.confirmDialog(title   = "A %s have accure" %record.funcName,
                                        message = record.message,
                                        button  = ['Dismiss'],
                                        messageAlign = "left")

        else:
            sys.stdout.write(msg+"\n")


## -----------------------------------------------------------------------------
# NukeHandler
## -----------------------------------------------------------------------------
class NukeHandler(logging.Handler):
    '''
    Nuke specific handler - will emit warnings using nuke.warning()
    and critical and fatal levels will popup a warning dialog so artists
    won't miss important errors.
    '''
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):

        # Formated message:
        msg = self.format(record)

        if record.funcName == "warning":
            nuke.warning(msg)

        elif record.funcName in [ "critical", "fatal" ]:
            nuke.error(msg)
            nuke.message(record.message)

        else:
            sys.stdout.write(msg)


## -----------------------------------------------------------------------------
# _name__
## -----------------------------------------------------------------------------
if __name__ == '__main__':
    ## Test code:

    log = getLogger( "logger_name", shell=True )
    log.setLevel( logging.DEBUG )
    log.debug('debug')
    log.info('info')
    log.warning('warning')
    log.fatal('fatal')
