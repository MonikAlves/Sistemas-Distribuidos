module Demo
{
    sequence<string> StringSeq;

    interface Printer
    {
        string printString(string s);

        // Novos metodos
        string toUpper(string s);
        int countWords(string s);
        StringSeq getHistory();
    }
}
