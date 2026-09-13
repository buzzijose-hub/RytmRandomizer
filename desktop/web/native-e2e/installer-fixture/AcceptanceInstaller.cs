using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;

[assembly: AssemblyTitle("RytmUpdaterAcceptanceInstaller")]
[assembly: AssemblyProduct("RytmUpdaterAcceptanceFixture")]
[assembly: AssemblyVersion("1.35.1.0")]

internal static class AcceptanceInstaller
{
    private static int Main(string[] args)
    {
        AcceptancePaths paths = null;
        int exitCode = 1;
        try
        {
            paths = new AcceptancePaths(args);
            string executable = Assembly.GetExecutingAssembly().Location;
            paths.RequireExtractedInstaller(executable);
            string artifactHash = AcceptancePaths.Hash(File.ReadAllBytes(executable));
            if (artifactHash != AcceptancePaths.Text(paths.Manifest, "installer_sha256"))
                throw new InvalidDataException("installer byte identity mismatch");
            if (Array.IndexOf(args, "/P") < 0 || Array.IndexOf(args, "/UPDATE") < 0)
                throw new InvalidDataException("plugin install arguments missing");
            bool restart = Array.IndexOf(args, "/R") >= 0;
            if (restart != (Array.IndexOf(args, "/ARGS") >= 0))
                throw new InvalidDataException("plugin restart arguments disagree");
            var start = paths.ReadJson("handoff-start.json");
            var boundary = paths.ReadJson("handoff-boundary.json");
            int parentPid = AcceptancePaths.Number(start, "parent_pid");
            int sidecarPid = AcceptancePaths.Number(start, "sidecar_pid");
            if (AcceptancePaths.Number(boundary, "parent_pid") != parentPid ||
                !(bool)boundary["shutdown_requested"] ||
                AcceptancePaths.Text(boundary, "artifact_sha256") != artifactHash ||
                AcceptancePaths.Alive(sidecarPid))
                throw new InvalidDataException("sidecar must be reaped before installer handoff");
            paths.AppendEvent("installer-events.jsonl", new { pid = Process.GetCurrentProcess().Id, sidecar_stopped = true });
            AcceptancePaths.WaitStopped(parentPid);
            byte[] successor;
            using (var resource = Assembly.GetExecutingAssembly().GetManifestResourceStream("Acceptance.Successor"))
            using (var buffer = new MemoryStream())
            {
                if (resource == null) throw new InvalidDataException("inert successor resource missing");
                resource.CopyTo(buffer);
                successor = buffer.ToArray();
            }
            string successorHash = AcceptancePaths.Hash(successor);
            if (successorHash != AcceptancePaths.Text(paths.Manifest, "successor_sha256") ||
                AcceptancePaths.Hash(File.ReadAllBytes(paths.ShellPath)) != AcceptancePaths.Text(paths.Manifest, "shell_sha256"))
                throw new InvalidDataException("fixture replacement identity mismatch");
            // The sole replacement target is the copied test shell, after its
            // process and passive backend have both exited. No install/registry API.
            using (var file = new FileStream(paths.ShellPath, FileMode.Create, FileAccess.Write, FileShare.None))
                file.Write(successor, 0, successor.Length);
            if (AcceptancePaths.Hash(File.ReadAllBytes(paths.ShellPath)) != successorHash)
                throw new InvalidDataException("replacement hash mismatch");
            int? restartedPid = null;
            if (restart)
            {
                var info = new ProcessStartInfo(paths.ShellPath, paths.SuccessorArguments());
                info.UseShellExecute = false;
                info.CreateNoWindow = true;
                using (var child = Process.Start(info))
                {
                    if (child == null) throw new InvalidDataException("successor did not start");
                    restartedPid = child.Id;
                    if (!child.WaitForExit(10000) || child.ExitCode != 0)
                        throw new InvalidDataException("successor did not complete");
                }
            }
            paths.WriteOnce("installer-receipt.json", new {
                passed = true, pid = Process.GetCurrentProcess().Id, parent_pid = parentPid,
                sidecar_pid = sidecarPid, sidecar_stopped_before_install = true,
                parent_exited_before_replace = true, artifact_sha256 = artifactHash,
                replacement_sha256 = successorHash, restart_requested = restart, successor_pid = restartedPid,
                arguments = args, replaced_file = "fixture-shell.exe"
            });
            exitCode = 0;
        }
        catch (Exception error)
        {
            // A failed receipt must still exit without a Windows crash dialog.
            try { if (paths != null) paths.WriteOnce("installer-error.json", new { passed = false, reason = error.GetType().Name }); }
            catch (Exception) { }
        }
        finally
        {
            try { if (paths != null) paths.WriteOnce("installer-exit.json", new { pid = Process.GetCurrentProcess().Id, exit_code = exitCode }); }
            catch (Exception) { exitCode = 1; }
        }
        return exitCode;
    }
}
