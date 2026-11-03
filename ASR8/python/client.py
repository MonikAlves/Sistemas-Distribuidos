import sys, Ice
import Demo

communicator = Ice.initialize(sys.argv)

# IP do servidor passado na linha de comando (python3 client.py <IP>)
host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

base = communicator.stringToProxy("SimplePrinter:tcp -h " + host + " -p 5678")
printer = Demo.PrinterPrx.checkedCast(base)
if not printer:
    raise RuntimeError("Invalid proxy")

print("Cliente Python -> servidor:", printer.getPlatform())

rep = printer.printString("Hello World from Python!")
print(rep)
rep = printer.toUpper("Hello World from Python!")
print(rep)
rep = printer.countWords("Hello World from Python client")
print(rep)
print(printer.getHistory())

communicator.destroy()
