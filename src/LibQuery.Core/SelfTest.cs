// 无 UI 冒烟自检：Core 全链路（FTS 能力 → 导出 → 建库/四种检索 → 批量/取消 → 导入）。
// 供 exe --selftest 与 CI 使用。PASS 退出码 0，FAIL 退出码 1。
// WinExe 无控制台：报告同时写入 CWD 的 selftest_result.txt，CI 以报告文件 + 退出码双重判定
//（对应 Python 版 --selfcheck 的 selfcheck_result.txt 约定）。

using System.Data;
using System.Globalization;
using System.Text;
using Microsoft.Data.Sqlite;
using MiniExcelLibs;

namespace LibQuery.Core;

public static class SelfTest
{
    public static int Run()
    {
        var workDir = Path.Combine(
            Path.GetTempPath(), "libquery-selftest-" + Guid.NewGuid().ToString("N"));
        var reportPath = Path.Combine(Environment.CurrentDirectory, "selftest_result.txt");
        try
        {
            Directory.CreateDirectory(workDir);
            File.WriteAllText(reportPath, "selfcheck started\n");  // 先落启动标记：区分未运行与运行到一半崩溃
            var log = new List<string>();
            RunChecks(workDir, log);
            var report = "LibQuery 自检: " + string.Join(" | ", log);
            try { Console.WriteLine(report); } catch { /* 无控制台时静默 */ }
            File.WriteAllText(reportPath, report + Environment.NewLine + "SELFTEST PASS" + Environment.NewLine);
            return 0;
        }
        catch (Exception e)
        {
            var msg = $"SELFTEST FAIL: {e.Message}";
            try
            {
                Console.WriteLine(msg);
                File.WriteAllText(reportPath, msg + Environment.NewLine);
            }
            catch { /* 报告写不进去时仅靠退出码判定 */ }
            return 1;
        }
        finally
        {
            try { Directory.Delete(workDir, recursive: true); } catch { /* 清理失败不影响结果 */ }
        }
    }

    private static void Assert(bool cond, string message)
    {
        if (!cond)
            throw new InvalidOperationException("断言失败: " + message);
    }

    private static void RunChecks(string dir, List<string> log)
    {
        // ---- 1. FTS5/trigram 能力（Microsoft.Data.Sqlite 内嵌 e_sqlite3）----
        Assert(Db.SupportsFtsTrigram(), "内嵌 SQLite 不支持 FTS5/trigram");
        using (var probe = Db.Open(":memory:"))
            log.Add($"sqlite={probe.ServerVersion} fts5_trigram=True");

        var outRoot = Path.Combine(dir, "output");

        // ---- 2. 文件名清洗 ----
        Assert(Exporter.CleanName("a/b:c*?\"<>|") == "a-b-c------", "非法字符替换");
        Assert(Exporter.CleanName("正常关键词.xlsx") == "正常关键词.xlsx", "正常名保留");
        Assert(Exporter.CleanName("*") == "-", "单非法字符");
        Assert(Exporter.CleanName(new string('x', 300)) == new string('x', 100), "超长截断");
        log.Add("[2] 文件名清洗 OK");

        // ---- 3. CSV 导出 + 预览格式 ----
        using (var mem = Db.Open(":memory:"))
        {
            Exec(mem, "CREATE TABLE t(题名 TEXT, 索书号 TEXT)");
            Exec(mem, "INSERT INTO t VALUES ('题名A', 'TP/1'), ('题名B', 'TP/2')");
            using (var cmd = mem.CreateCommand())
            {
                cmd.CommandText = "SELECT * FROM t";
                using var r = cmd.ExecuteReader();
                var columns = Range(r);
                var res = Exporter.ExportRows("csv", "题名", "测试词", columns, r, outRoot);
                Assert(res.Rows == 2 && !res.Truncated, $"csv 行数: {res.Rows}");
                Assert(res.Path == Path.Combine(outRoot, "题名", "测试词.csv"), $"csv 路径: {res.Path}");
                var text = File.ReadAllText(res.Path);  // ReadAllText 自动识别并剥离 BOM
                var firstLine = text.Split('\n')[0].TrimEnd('\r');
                Assert(firstLine == "题名,索书号", $"csv 表头: {firstLine}");
                Assert(text.Contains("题名A") && text.Contains("TP/1"), "csv 内容");
                Assert(res.Head.Count == 2, "预览捕获");
                Assert(Exporter.FormatPreview(["A", "B"], [new object?[] { "a", null }]) == "A | B\na | ",
                    "预览格式（null → 空串）");
            }
        }
        log.Add("[3] CSV 导出/预览 OK");

        // ---- 4. xlsx 截断 + 空结果表头（MiniExcel DataReader 通道验证）----
        using (var mem = Db.Open(":memory:"))
        {
            Exec(mem, "CREATE TABLE t(题名 TEXT)");
            Exec(mem, "INSERT INTO t " + string.Join("\nUNION ALL\n",
                Enumerable.Range(0, 50).Select(i => $"SELECT 'row{i}'")));
            using (var cmd = mem.CreateCommand())
            {
                cmd.CommandText = "SELECT 题名 FROM t";
                using var r = cmd.ExecuteReader();
                var res = Exporter.ExportRows("xlsx", "题名", "trunc", ["题名"], r, outRoot, maxRowsOverride: 5);
                Assert(res.Truncated && res.Rows == 5, $"xlsx 截断: rows={res.Rows} truncated={res.Truncated}");
            }
            Assert(File.Exists(Path.Combine(outRoot, "题名", "trunc.xlsx")), "截断文件存在");
            Assert(CountSheetRows(Path.Combine(outRoot, "题名", "trunc.xlsx")) == 6, "xlsx 读回 = 表头+5 行");

            using (var cmd = mem.CreateCommand())
            {
                cmd.CommandText = "SELECT 题名 FROM t WHERE 0";
                using var r = cmd.ExecuteReader();
                var res = Exporter.ExportRows("xlsx", "题名", "empty", ["题名"], r, outRoot);
                Assert(res.Rows == 0 && !res.Truncated, "空结果行数");
            }
            Assert(CountSheetRows(Path.Combine(outRoot, "题名", "empty.xlsx")) == 1, "空结果仍有表头行");
        }
        log.Add("[4] xlsx 截断/空结果表头 OK");

        // ---- 5. 建库 → 四种检索 ----
        var synthDb = Path.Combine(dir, "synth.db");
        SynthDb.MakeBooksDb(synthDb, 200, withFts: true);
        var service = new LibraryService(synthDb, outRoot);
        var pieceSpec = SearchSpecs.All[0];
        var callNumSpec = SearchSpecs.All[1];
        var isbnSpec = SearchSpecs.All[2];
        var titleSpec = SearchSpecs.All[3];

        var rTitle = service.SearchSingle(titleSpec, "计算机网络", "csv");
        Assert(rTitle.Error is null, $"题名 FTS: {rTitle.Error}");
        Assert(rTitle.Rows == 25, $"题名 FTS 命中: {rTitle.Rows} != 25");
        Assert(rTitle.Preview is not null && rTitle.Preview.Contains("计算机网络"), "题名预览");
        Assert(File.Exists(Path.Combine(outRoot, "题名", "计算机网络.csv")), "题名输出文件");

        var rIsbn = service.SearchSingle(isbnSpec, "9787000000005", "csv");
        Assert(rIsbn.Rows == 1 && rIsbn.Preview!.Contains("9787000000005"), "ISBN 精确");

        var rCall = service.SearchSingle(callNumSpec, "TP311.13/1", "csv");
        Assert(rCall.Rows == 1, "索书号精确");

        var rPiece = service.SearchSingle(pieceSpec, "I247", "csv");
        Assert(rPiece.Rows == 50, $"切片 level_4: {rPiece.Rows} != 50");
        var rPiece2 = service.SearchSingle(pieceSpec, "I247.5", "csv");
        Assert(rPiece2.Rows == 50, $"切片 level_5: {rPiece2.Rows} != 50");

        var rEmpty = service.SearchSingle(titleSpec, "   ", "csv");
        Assert(rEmpty.Messages[0].Contains("非法输入"), "空关键词");

        var rQuote = service.SearchSingle(titleSpec, "导\"论", "csv");
        Assert(rQuote.Error is null, "FTS 短语含双引号");

        log.Add("[5] 建库/四模式检索 OK");

        // ---- 6. 批量 + 文件 + 取消 ----
        var progressLog = new List<(int Done, int Total)>();
        var rb = service.SearchBatch(isbnSpec,
            ["9787000000000", "9787000000001", ""], "csv",
            (d, t) => progressLog.Add((d, t)));
        Assert(rb.Error is null && rb.Items.Count == 2, $"批量条目: {rb.Items.Count}");
        Assert(progressLog.SequenceEqual([(1, 2), (2, 2)]), "批量进度回调");
        Assert(File.Exists(Path.Combine(outRoot, "ISBN", "9787000000000.csv")), "批量文件 1");
        Assert(File.Exists(Path.Combine(outRoot, "ISBN", "9787000000001.csv")), "批量文件 2");

        var keyFile = Path.Combine(dir, "keys.txt");
        File.WriteAllLines(keyFile, ["9787000000000", "", "9787000000001"]);
        var rf = service.SearchBatchFromFile(isbnSpec, keyFile, "csv");
        Assert(rf.Error is null && rf.Items.Count == 2, "TXT 文件批量（空行剔除）");

        using (var cts = new CancellationTokenSource())
        {
            cts.Cancel();  // 预先置位：立即取消
            var rc = service.SearchBatch(isbnSpec, ["9787000000000", "9787000000001"], "csv",
                cancel: cts.Token);
            Assert(rc.Cancelled && rc.Items.Count == 0, "预取消批量");
        }
        log.Add("[6] 批量/文件/取消 OK");

        // ---- 7. Excel 导入（列重命名 + 数值 ISBN 规整 + FTS）----
        var fixture = Path.Combine(dir, "馆藏.xlsx");
        // 字典行保留逐格类型：第 3 行 标准号 为数值（对应 Excel 未按文本存储的典型情况）
        var fixtureRows = new List<Dictionary<string, object?>>
        {
            new()
            {
                ["题名"] = "数据结构教程", ["索书号"] = "TP311.13/1", ["标准号"] = "9787030123456",
                ["出版年"] = "2019", ["分级一"] = "T", ["分级二"] = "TP", ["分级三"] = "TP3",
                ["分级四"] = "TP31", ["分级五"] = "TP311.13", ["分级六"] = "TP311.13", ["分级七"] = "TP311.13/1",
            },
            new()
            {
                ["题名"] = "古代文学史", ["索书号"] = "I209/2", ["标准号"] = "9787100100000",
                ["出版年"] = "2013", ["分级一"] = "I", ["分级二"] = "I2", ["分级三"] = "I20",
                ["分级四"] = "I209", ["分级五"] = "I209", ["分级六"] = "I209", ["分级七"] = "I209/2",
            },
            new()
            {
                ["题名"] = "操作系统导论", ["索书号"] = "TP316/3", ["标准号"] = 9787111544937d,
                ["出版年"] = "2016", ["分级一"] = "T", ["分级二"] = "TP", ["分级三"] = "TP3",
                ["分级四"] = "TP31", ["分级五"] = "TP316", ["分级六"] = "TP316", ["分级七"] = "TP316/3",
            },
        };
        MiniExcel.SaveAs(fixture, fixtureRows);

        var importedDb = Path.Combine(dir, "imported.db");
        var importMessages = new List<string>();
        var summary = Importer.ImportExcel(fixture, importedDb, importMessages.Add);
        Assert(summary.Rows == 3, $"导入行数: {summary.Rows}");
        Assert(summary.Columns[4] == "level_1" && summary.Columns[10] == "level_7", "列重命名");
        Assert(importMessages.Any(m => m.Contains("FTS5")), "FTS 构建提示");

        using (var conn = Db.Open(importedDb))
        {
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = "PRAGMA table_info(books)";
                using var r = cmd.ExecuteReader();
                var cols = new List<string>();
                while (r.Read())
                    cols.Add(r.GetString(1));
                Assert(cols.Skip(4).SequenceEqual(
                    Enumerable.Range(1, 7).Select(i => $"level_{i}")), "表结构 level_N");
            }
            Assert(Scalar(conn, "SELECT COUNT(*) FROM books") == 3, "导入计数");
            Assert(ScalarText(conn, "SELECT \"标准号\" FROM books WHERE \"题名\" = '操作系统导论'")
                == "9787111544937", "数值 ISBN 去尾差");
            Assert(Scalar(conn, "SELECT COUNT(*) FROM books_fts WHERE books_fts MATCH '\"数据结构\"'")
                == 1, "FTS 可查");
        }

        Importer.ImportExcel(fixture, importedDb);  // 重复导入 = 破坏性重建
        using (var conn2 = Db.Open(importedDb))
        {
            Assert(Scalar(conn2, "SELECT COUNT(*) FROM books") == 3, "重建后计数");
            Assert(Scalar(conn2, "SELECT COUNT(*) FROM books_fts") == 3, "重建后 FTS 计数");
        }
        log.Add("[7] Excel 导入/FTS OK");
    }

    // ---- 夹具与工具 ----

    /// <summary>统计 xlsx 首表行数（含表头），用于导出读回验证。</summary>
    private static int CountSheetRows(string xlsxPath)
    {
        using var stream = File.Open(xlsxPath, FileMode.Open, FileAccess.Read, FileShare.Read);
        using var reader = ExcelDataReader.ExcelReaderFactory.CreateReader(stream);
        int rows = 0;
        while (reader.Read())
            rows++;
        return rows;
    }

    private static void Exec(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        cmd.ExecuteNonQuery();
    }

    private static long Scalar(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        return Convert.ToInt64(cmd.ExecuteScalar());
    }

    private static string ScalarText(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        return Convert.ToString(cmd.ExecuteScalar()) ?? "";
    }

    private static List<string> Range(System.Data.Common.DbDataReader r) =>
        Enumerable.Range(0, r.FieldCount).Select(r.GetName).ToList();
}
