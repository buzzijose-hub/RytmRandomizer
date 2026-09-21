// Test-only Windows process-handoff fixture. No registry, network or MIDI APIs.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

internal sealed class AcceptancePaths
{
    internal readonly string Root;
    internal readonly string Nonce;
    internal readonly Dictionary<string, object> Manifest;
    internal string ShellPath { get { return OwnedFile("fixture-shell.exe"); } }

    internal AcceptancePaths(string[] args)
    {
        string root = Argument(args, "--fixture-root");
        Nonce = Argument(args, "--fixture-nonce");
        Guid parsed;
        if (!Guid.TryParseExact(Nonce, "D", out parsed) || !Path.IsPathRooted(root))
            throw new InvalidDataException("fixture identity missing");
        Root = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
        if (!new DirectoryInfo(Root).Name.StartsWith("rytm-native-update-", StringComparison.Ordinal))
            throw new InvalidDataException("fixture directory name refused");
        CheckNoLinks(Root);
        if (File.ReadAllText(OwnedFile("acceptance-marker")) != Nonce)
            throw new InvalidDataException("fixture marker mismatch");
        Manifest = ReadJson("handoff-acceptance.json");
        if (Text(Manifest, "nonce") != Nonce)
            throw new InvalidDataException("fixture manifest mismatch");
    }

    private static string Argument(string[] args, string name)
    {
        string value = null;
        for (int index = 0; index < args.Length; index++)
        {
            if (args[index] != name) continue;
            if (value != null || index + 1 >= args.Length)
                throw new InvalidDataException("duplicate or missing fixture argument");
            value = args[++index];
        }
        if (value == null) throw new InvalidDataException("fixture argument missing");
        return value;
    }

    internal string OwnedFile(string name)
    {
        if (name != Path.GetFileName(name)) throw new InvalidDataException("fixture basename required");
        string result = Path.GetFullPath(Path.Combine(Root, name));
        if (!result.StartsWith(Root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("fixture path escaped");
        CheckNoLinks(result);
        return result;
    }

    internal void RequireExtractedInstaller(string path)
    {
        string prefix = Path.Combine(Root, "plugin-temp") + Path.DirectorySeparatorChar;
        if (!Path.GetFullPath(path).StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("installer must be extracted inside the fixture");
        CheckNoLinks(path);
    }

    private static void CheckNoLinks(string path)
    {
        string current = Path.GetFullPath(path);
        while (!String.IsNullOrEmpty(current))
        {
            if ((File.Exists(current) || Directory.Exists(current)) &&
                (File.GetAttributes(current) & FileAttributes.ReparsePoint) != 0)
                throw new InvalidDataException("fixture links or junctions refused");
            current = Path.GetDirectoryName(current);
        }
    }

    internal Dictionary<string, object> ReadJson(string name)
    {
        return new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(
            File.ReadAllText(OwnedFile(name)));
    }

    internal void WriteOnce(string name, object value)
    {
        using (var stream = new FileStream(OwnedFile(name), FileMode.CreateNew, FileAccess.Write, FileShare.Read))
        using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
            writer.Write(new JavaScriptSerializer().Serialize(value));
    }

    internal void AppendEvent(string name, object value)
    {
        using (var stream = new FileStream(OwnedFile(name), FileMode.Append, FileAccess.Write, FileShare.Read))
        using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
            writer.WriteLine(new JavaScriptSerializer().Serialize(value));
    }

    internal static string Text(Dictionary<string, object> value, string key)
    {
        return (string)value[key];
    }

    internal static int Number(Dictionary<string, object> value, string key)
    {
        return Convert.ToInt32(value[key]);
    }

    internal static string Hash(byte[] bytes)
    {
        using (var hash = SHA256.Create())
            return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
    }

    internal static bool Alive(int pid)
    {
        try { using (var process = Process.GetProcessById(pid)) return !process.HasExited; }
        catch (ArgumentException) { return false; }
    }

    internal static void WaitStopped(int pid)
    {
        var deadline = DateTime.UtcNow.AddSeconds(20);
        while (Alive(pid))
        {
            if (DateTime.UtcNow > deadline) throw new InvalidDataException("fixture parent did not exit");
            Thread.Sleep(50);
        }
    }

    internal string SuccessorArguments()
    {
        return "--fixture-root \"" + Root + "\" --fixture-nonce " + Nonce;
    }
}
