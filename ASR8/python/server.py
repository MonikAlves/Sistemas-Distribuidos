import sys, platform, Ice
import Demo

class PrinterI(Demo.Printer):
    def __init__(self):
        self.history = []

    def printString(self, s, current=None):
        print(s)
        self.history.append(s)
        return s + "*"

    def toUpper(self, s, current=None):
        print("toUpper:", s)
        return s.upper()

    def countWords(self, s, current=None):
        print("countWords:", s)
        return len(s.split())

    def getHistory(self, current=None):
        return self.history

    # Novo metodo: informa a linguagem e a plataforma do servidor
    def getPlatform(self, current=None):
        return "Python " + platform.python_version() + " / Ice " + Ice.stringVersion() + " / " + platform.system()

communicator = Ice.initialize(sys.argv)

adapter = communicator.createObjectAdapterWithEndpoints("SimpleAdapter", "default -p 5678")
object = PrinterI()
adapter.add(object, Ice.Identity("SimplePrinter"))
adapter.activate()

print("Servidor Python pronto na porta 5678", flush=True)
communicator.waitForShutdown()
