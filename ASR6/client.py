import sys, Ice
import Demo
 
communicator = Ice.initialize(sys.argv)

base = communicator.stringToProxy("SimplePrinter:tcp -h 34.203.80.210 -p 5678")
printer = Demo.PrinterPrx.checkedCast(base)
if not printer:
    raise RuntimeError("Invalid proxy")

printer.printString("Hello World!")

print(printer.toUpper("Hello World!"))
print(printer.countWords("Hello World from Ice!"))
print(printer.getHistory())
