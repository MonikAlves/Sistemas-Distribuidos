import java.util.ArrayList;
import java.util.List;

import com.zeroc.Ice.Current;

public class PrinterI implements Demo.Printer
{
    private final List<String> history = new ArrayList<>();

    @Override
    public String printString(String s, Current current)
    {
        System.out.println(s);
        history.add(s);
        return s + "*";
    }

    @Override
    public String toUpper(String s, Current current)
    {
        System.out.println("toUpper: " + s);
        return s.toUpperCase();
    }

    @Override
    public int countWords(String s, Current current)
    {
        System.out.println("countWords: " + s);
        String t = s.trim();
        return t.isEmpty() ? 0 : t.split("\s+").length;
    }

    @Override
    public String[] getHistory(Current current)
    {
        return history.toArray(new String[0]);
    }

    @Override
    public String getPlatform(Current current)
    {
        return "Java " + System.getProperty("java.version") + " / Ice " + com.zeroc.Ice.Util.stringVersion()
            + " / " + System.getProperty("os.name");
    }
}
