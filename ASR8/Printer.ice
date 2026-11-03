module Demo
{
    sequence<string> StringSeq;

    interface Printer
    {
        string printString(string s);
        string toUpper(string s);
        int countWords(string s);
        StringSeq getHistory();

        // Novo metodo: informa a linguagem e a plataforma do servidor
        string getPlatform();
    }
}
