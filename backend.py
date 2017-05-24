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
        self._task = {
                        'task0': ['tarea0', 'Subtarea0'],
                        'task1': ['tarea1', 'Subtarea1'],
                    }
        self._visitors = 0;
        #Conectar con base de datos y rescatar info
        #global conn
        #conn = sqlite3.connect('example.db')
        #global c
        #c = conn.cursor()
        #Insecure
        #c.execute('CREATE TABLE IF NOT EXISTS Tasks (created TEXT, data TEXT')
        #c.execute('SELECT * FROM Tasks ORDER BY created')
        #data = c.fetchone()
        #self._task = json.loads(data[1])
        #c.execute("DELETE FROM Tasks WHERE created = '%s'" %data[0])
        #conn.commit()

    #VISITORS
    @wamp.register(u'io.crossbar.app.getvisitors')
    def getvisitor(self):
        return self._visitors

    #TASK
    @wamp.register(u'io.crossbar.app.gettask')
    def gettask(self):
        return [[len(self._task),self._task]]


    @wamp.register(u"io.crossbar.app.createtask")
    def submittask(self, JSONobjectID, JSONobject):

        sub = JSONobjectID.split(".")
        if (len(sub) < 2):

            #Añadir el elemento la variable de python
            self._task[JSONobjectID] = [JSONobject]
            #item = {}
            #item[JSONobjectID] = JSONobject


        else:
            self._task[sub[0]][int(sub[1])] = JSONobject

        #Publico el JSON sin tratamiento hacia las demás instancias
        #self.publish('io.crossbar.app.oncreatetask', [len(self._task), self._task])
        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])



    @wamp.register(u"io.crossbar.app.delall")
    def delall(self):
        self._task = {}
        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])
        #return self._task


    @wamp.register(u"io.crossbar.app.saveall")
    def saveall(self):
        #Conexión a base de datos para salvar el dict _task
        self.publish('io.crossbar.app.updatesavetime')
        #return self._task


    @wamp.register(u"io.crossbar.app.deltask")
    def deltask(self, id):

        sub = id.split(".")
        if (len(sub) < 2):
            ##Eliminar tareas desde la indicada
            x = int(re.search(r'\d+', id).group())
            if ((len(self._task)-1) > x):
                while (x < (len(self._task)-1)):

                    #convierto en json para cambiar el taskID
                    #myJSON = json.loads(self._task["task"+str(x+1)])

                    #modifico el id al correcto y varios atributos
                    #myJSON['node']['id'] = "task"+str(x)
                    #myJSON['node']['attributes']['id'] = "task"+str(x)
                    #myJSON['node']['childNodes'][0]['childNodes'][0]['data'] = str(x)
                    #myJSON['node']['childNodes'][0]['childNodes'][0]['nodeValue'] = str(x)

                    #vuelvo a convertir en str
                    self._task["task"+str(x)] = self._task["task"+str(x+1)]

                    #Aumento contador
                    x += 1

                del self._task["task"+str(x)]
            else:
                del self._task[id]

        else:
            self._task[sub[0]].pop(int(sub[1]))


        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])
        #return self._task


    @wamp.register("io.crossbar.app.nest")
    def nest(self, source, target):

        for i in source[1]:
            self._task[target[0]].append(i)

        self.deltask(source[0])
        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])


    @wamp.register("io.crossbar.app.reorder")
    def reorder(self, source, target):

        sourceID = int(re.search(r'\d+', source[0]).group())
        targetID = int(re.search(r'\d+', target[0]).group())

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


    @inlineCallbacks
    def onJoin(self, details):

        def onconnect(msg):
            self._visitors += 1
            self.publish('io.crossbar.app.visitorupdate', self._visitors)
            return self._visitors

        conn = yield self.subscribe(onconnect, "wamp.session.on_join")
        print(conn)

        def ondisconnect(msg):
            self._visitors -= 1
            if self._visitors < 0:
                self._visitors = 0;
            self.publish('io.crossbar.app.visitorupdate', self._visitors)
            return self._visitors

        disconn = yield self.subscribe(ondisconnect, "wamp.session.on_leave")
        print(disconn)


        res = yield self.register(self)
        print("appBackend: {} procedures registered!".format(len(res)))



    def onLeave(self, session):
        print("A connection has been lost")
