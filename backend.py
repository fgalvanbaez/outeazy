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

import re
import json
import sqlite3

class appBackend(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.init()

    def init(self):
        #variable para almacenar las tareas
        self._task = {
                        'task0': ['tarea0', 'Subtarea0'],
                        'task1': ['tarea1', 'Subtarea1'],
                    }
        #variable para almacenar las sesiones conectadas
        self._visitors = 0;


    """
    función que sirve para obtener el número de
    de sesiones conectadas desde el frontend
    """
    @wamp.register(u'io.crossbar.app.getvisitors')
    def getvisitor(self):
        self.log.info(" calling 'getvisitors' return self._visitors {visitors}", visitors=self._visitors)
        return self._visitors

    """
    función que sirve para obtener el número de
    de tareas existentes y un dict con todas las
    tareas
    """
    @wamp.register(u'io.crossbar.app.gettask')
    def gettask(self):
        self.log.info(" calling 'gettask' return [[len(self._task),self._task]]")
        return [[len(self._task),self._task]]

    """
    función que sirve para crear una tarea nueva en
    la variable _task. Luego publica la variable _task
    actualizada y el nuevo número de tareas
    """
    @wamp.register(u"io.crossbar.app.createtask")
    def submittask(self, JSONobjectID, JSONobject):
        self.log.info(" calling 'createtask' with id {id}", id=JSONobjectID)
        sub = JSONobjectID.split(".")
        self._task[sub[0]] = JSONobject
        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])

    """
    función que sirve para eliminar completamente el
    contenido de la variable _task. Luego publica la variable _task
    actualizada y el nuevo número de tareas
    """
    @wamp.register(u"io.crossbar.app.delall")
    def delall(self):
        self.log.info(" calling 'delall'")
        self._task = {}
        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])

    """
    función que sirve para guardar el contenido de la
    variable _task (Not implemented)
    """
    @wamp.register(u"io.crossbar.app.saveall")
    def saveall(self):
        self.log.info(" calling 'saveall'")
        self.publish('io.crossbar.app.updatesavetime')

    """
    función que sirve para eliminar una tarea determinada.
    Luego publica la variable _task actualizada y el
    nuevo número de tareas
    """
    @wamp.register(u"io.crossbar.app.deltask")
    def deltask(self, id):
        self.log.info(" calling 'deltask' with id:{id}", id=id)
        sub = id.split(".")
        if (len(sub) < 2):
            ##Eliminar tareas desde la indicada
            x = int(re.search(r'\d+', id).group())
            if ((len(self._task)-1) > x):
                while (x < (len(self._task)-1)):
                    self._task["task"+str(x)] = self._task["task"+str(x+1)]
                    x += 1
                del self._task["task"+str(x)]
            else:
                del self._task[id]

        else:
            self._task[sub[0]].pop(int(sub[1]))


        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])
        #return self._task

    """
    función que sirve para anidar una tarea dentro de otra
    Luego publica la variable _task actualizada y el nuevo
    número de tareas
    """
    @wamp.register("io.crossbar.app.nest")
    def nest(self, source, target):
        self.log.info(" calling 'nest' with id:{id}", id=source[0])
        for i in source[1]:
            self._task[target[0]].append(i)

        self.deltask(source[0])
        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])

    """
    función que sirve para ordenar las tareas, debido a la funcion
    Drag'n'Drop en el frontend. Luego publica la variable _task
    actualizada y el nuevo número de tareas
    """
    @wamp.register("io.crossbar.app.reorder")
    def reorder(self, source, target):
        self.log.info(" calling 'reorder' with id:{id}", id=source[0])
        sourceID = int(re.search(r'\d+', source[0]).group())
        targetID = int(re.search(r'\d+', target[0]).group())
        sub = source[0].split(".")
        if (len(sub) > 1):
            self._task['task'+str(len(self._task))] = source[1]
            self._task[sub[0]].pop(int(sub[1]))
            sourceID = len(self._task)-1

        #Si bajo el elemento
        if (sourceID < targetID):
            x = sourceID
            while (x < targetID):
                self._task['task'+str(x)] = self._task['task'+str(x+1)]
                x += 1
            #finalmente se asigna el valor de la tarea movida en
            #el puesto que le corresponde
            self._task['task'+str(targetID)] = source[1]

        else:
            x = sourceID
            while (x > targetID):
                self._task['task'+str(x)] = self._task['task'+str(x-1)]
                x -= 1

            self._task['task'+str(targetID)] = source[1]

        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])


    """
    Lifecycle of component
    """
    def onConnect(self):
        self.log.info(" transport connected")
        self.join(self.config.realm)

    def onChallenge(self, challenge):
        self.log.info(" authentication challenge received")

    @inlineCallbacks
    def onJoin(self, details):

        self.log.info(" Session connected")
        def onconnect(msg):
            self._visitors += 1
            self.log.info(" publishing to 'visitorupdate' with _visitors {visitors}", visitors=self._visitors)
            self.publish('io.crossbar.app.visitorupdate', self._visitors)
            return self._visitors

        def ondisconnect(msg):
            self._visitors -= 1
            if self._visitors < 0:
                self._visitors = 0;

            self.log.info(" publishing to 'visitorupdate' with _visitors {visitors}", visitors=self._visitors)
            self.publish('io.crossbar.app.visitorupdate', self._visitors)
            return self._visitors

        try:
            conn = yield self.subscribe(onconnect, "wamp.session.on_join")
            self.log.info(" Subscription to {}" .format(conn.topic))
        except Exception as e:
            self.log.error(" could not subscribe to topic: {0}".format(e))

        try:
            disconn = yield self.subscribe(ondisconnect, "wamp.session.on_leave")
            self.log.info(" Subscription to {}" .format(disconn.topic))
        except Exception as e:
            self.log.error(" could not subscribe to topic: {0}".format(e))

        try:
            res = yield self.register(self)
            self.log.info(" appBackend: {} procedures registered!".format(len(res)))
            for i in res:
                self.log.info("    Functions register {}".format(i.procedure))
        except Exception as e:
            self.log.error(" could not register procedure: {0}".format(e))


    def onLeave(self, session):
        self.log.info(" Session left")

    def onDisconnect(self):
        self.log.info(" transport disconnected")
