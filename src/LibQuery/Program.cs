// 图书馆馆藏条目检索系统入口。CLI 分支：
//   --selftest      无 UI 冒烟（CI/交付验收用，报告写 CWD\selftest_result.txt）
//   --rebuild-fts   为存量数据库补建 FTS5 题名索引（对应 Python 版 scripts/rebuild_fts.py）
// 其余启动 WinForms 主窗口。

using System.Runtime.InteropServices;
using LibQuery.Core;

namespace LibQuery;

internal static class Program
{
    [DllImport("kernel32.dll")]
    private static extern bool AttachConsole(int processId);

    private const int AttachParentProcess = -1;

    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length > 0 && args[0] == "--selftest")
            return Core.SelfTest.Run();
        if (args.Length > 0 && args[0] == "--rebuild-fts")
            return RebuildFtsCli(args);

        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
        return 0;
    }

    private static int RebuildFtsCli(string[] args)
    {
        // WinExe 无控制台：附着父进程控制台，输出才能落到 cmd 窗口
        try { AttachConsole(AttachParentProcess); } catch { /* 无父控制台时静默 */ }

        bool force = args.Contains("--force");
        var paths = args.Where(a => !a.StartsWith("--")).ToList();
        var dbPath = paths.Count > 0 ? paths[0] : AppPaths.DbPath;
        var code = LibraryService.RebuildFts(dbPath, force, Console.WriteLine);
        Console.Out.Flush();
        return code;
    }
}
