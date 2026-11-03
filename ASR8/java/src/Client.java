import java.util.Arrays;

import com.zeroc.Ice.Communicator;
import com.zeroc.Ice.ObjectPrx;
import com.zeroc.Ice.Util;

import Demo.PrinterPrx;

public class Client
{
    public static void main(String[] args)
    {
        try(Communicator communicator = Util.initialize(args))
        {
            String host = args.length > 0 ? args[0] : "127.0.0.1";

            ObjectPrx base = communicator.stringToProxy("SimplePrinter:tcp -h " + host + " -p 5678");
            PrinterPrx printer = PrinterPrx.checkedCast(base);
            if(printer == null)
            {
                throw new Error("Invalid proxy");
            }

            System.out.println("Cliente Java -> servidor: " + printer.getPlatform());
            System.out.println(printer.printString("Hello World from Java!"));
            System.out.println(printer.toUpper("Hello World from Java!"));
            System.out.println(printer.countWords("Hello World from Java client"));
            System.out.println(Arrays.toString(printer.getHistory()));
        }
    }
}
