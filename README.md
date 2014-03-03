cg-logging
==========

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
