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
        self._task = {}
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

        #Añadir el elemento la variable de python
        self._task[JSONobjectID] = JSONobject
        #item = {}
        #item[JSONobjectID] = JSONobject

        #Publico el JSON sin tratamiento hacia las demás instancias
        self.publish('io.crossbar.app.oncreatetask', [len(self._task), self._task])
        #return self._task


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

        """
        Eliminar tareaX
        desde tareaX hasta final de tareas
            tareaX = tareaX+1
        del tareaX

        """

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

                """#busco la subcadena taskID y lo reemplazo por el correcto
                mySTR = self._task["task"+str(x+1)].replace(("task"+str(x+1)), ("task"+str(x)))

                #Actualizo el valor en el correcto
                self._task["task"+str(x)] = mySTR"""

                #Aumento contador
                x += 1

            del self._task["task"+str(x)]
        else:
            del self._task[id]

        self.publish('io.crossbar.app.updateall', [len(self._task), self._task])
        #return self._task


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
