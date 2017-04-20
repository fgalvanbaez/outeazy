###############################################################################
##
##  Copyright (C) 2014, Tavendo GmbH and/or collaborators. All rights reserved.
##
##  Redistribution and use in source and binary forms, with or without
##  modification, are permitted provided that the following conditions are met:
##
##  1. Redistributions of source code must retain the above copyright notice,
##     this list of conditions and the following disclaimer.
##
##  2. Redistributions in binary form must reproduce the above copyright notice,
##     this list of conditions and the following disclaimer in the documentation
##     and/or other materials provided with the distribution.
##
##  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
##  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
##  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
##  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
##  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
##  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
##  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
##  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
##  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
##  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
##  POSSIBILITY OF SUCH DAMAGE.
##
###############################################################################

from twisted.internet.defer import inlineCallbacks
from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession
#from autobahn.asincio.wamp import ApplicationSession
from twisted.internet import reactor

import json

class appBackend(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.init()

    def init(self):
        self._task = {}
        self._visitors = 0;

    #VISITORS
    @wamp.register(u'io.crossbar.app.getvisitors')
    def getvisitor(self):
        return self._visitors

    #TASK
    @wamp.register(u'io.crossbar.app.gettask')
    def gettask(self):
        return [len(self._task),self._task]


    @wamp.register(u"io.crossbar.app.updatetask")
    def submittask(self, JSONobjectID, JSONobject):

        #Añadir el elemento la variable de python
        self._task[JSONobjectID] = JSONobject

        #Publico el JSON sin tratamiento hacia las demás instancias
        self.publish('io.crossbar.app.onupdatetask', [len(self._task), JSONobject])
        return self._task


    @inlineCallbacks
    def onJoin(self, details):

        def onconnect(msg):
            self._visitors += 1
            self.publish('io.crossbar.app.visitorupdate', [self._visitors])
            return self._visitors

        conn = yield self.subscribe(onconnect, "wamp.session.on_join")
        print(conn)

        def ondisconnect(msg):
            self._visitors -= 1
            if self._visitors < 0:
                self._visitors = 0;
            self.publish('io.crossbar.app.visitorupdate', [self._visitors])
            return self._visitors

        disconn = yield self.subscribe(ondisconnect, "wamp.session.on_leave")
        print(disconn)


        res = yield self.register(self)
        print("appBackend: {} procedures registered!".format(len(res)))



    def onLeave(self, session):
        print("A connection has been lost")
