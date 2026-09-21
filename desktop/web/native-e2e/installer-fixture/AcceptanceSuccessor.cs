using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;

[assembly: AssemblyTitle("RytmUpdaterAcceptanceSuccessor")]
[assembly: AssemblyProduct("RytmUpdaterAcceptanceFixture")]
[assembly: AssemblyVersion("1.35.1.0")]

internal static class AcceptanceSuccessor
{
    private static int Main(string[] args)
    {
        try { return RecordRestart(args); }
        catch (Exception) { return 1; }
    }

    private static int RecordRestart(string[] args)
    {
        var paths = new AcceptancePaths(args);
        string executable = Path.GetFullPath(Assembly.GetExecutingAssembly().Location);
        if (!String.Equals(executable, paths.ShellPath, StringComparison.OrdinalIgnoreCase)) return 1;
        string hash = AcceptancePaths.Hash(File.ReadAllBytes(executable));
        if (hash != AcceptancePaths.Text(paths.Manifest, "successor_sha256")) return 1;
        var receipt = new { pid = Process.GetCurrentProcess().Id, sha256 = hash, version = "1.35.1", nonce = paths.Nonce };
        paths.AppendEvent("restart-events.jsonl", receipt);
        paths.WriteOnce("restart-receipt.json", receipt);
        return 0;
    }
}
