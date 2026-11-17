// 检索编排层：连接生命周期与单次/批量检索入口。
// 移植自 Python 版 lib_query/service.py：本层方法均设计为可在工作线程中调用；
// 每次调用自建连接、用完即关（检索以读为主，多任务并发由 SQLite 读并发天然支持）。

using Microsoft.Data.Sqlite;

namespace LibQuery.Core;

public sealed class LibraryService
{
    public string DbPath { get; }

    /// <summary>导出根目录；null = AppPaths.OutputDir（测试注入用）。</summary>
    public string? OutputRoot { get; }

    private const string NoDbMessage = "数据库不存在，请先导入馆藏 Excel 文件。";

    public LibraryService(string? dbPath = null, string? outputRoot = null)
    {
        DbPath = dbPath ?? AppPaths.DbPath;
        OutputRoot = outputRoot;
    }

    public bool Exists() => File.Exists(DbPath);

    public int RecordCount()
    {
        if (!Exists())
            return 0;
        using var conn = Db.Open(DbPath);
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT COUNT(*) FROM books";
        return Convert.ToInt32(cmd.ExecuteScalar());
    }

    public bool HasFts()
    {
        if (!Exists())
            return false;
        using var conn = Db.Open(DbPath);
        return Db.TableExists(conn, "books_fts");
    }

    public ImportSummary ImportExcel(string excelPath, Action<string>? progress = null) =>
        Importer.ImportExcel(excelPath, DbPath, progress);

    /// <summary>对存量数据库补建索引与 FTS5 题名索引（对应 scripts/rebuild_fts.py）。</summary>
    public static int RebuildFts(string dbPath, bool force, Action<string>? log = null)
    {
        if (!File.Exists(dbPath))
        {
            log?.Invoke($"数据库不存在: {dbPath}");
            return 1;
        }
        using var conn = Db.Open(dbPath);
        if (!Db.TableExists(conn, "books"))
        {
            log?.Invoke("数据库中没有 books 表，请先通过程序导入馆藏 Excel。");
            return 1;
        }
        if (Db.TableExists(conn, "books_fts") && !force)
        {
            log?.Invoke("已存在 books_fts 索引；如需重建请加 --force。");
            return 0;
        }
        if (Db.TableExists(conn, "books_fts"))
            Execute(conn, "DROP TABLE IF EXISTS books_fts");

        var t0 = System.Diagnostics.Stopwatch.StartNew();
        Importer.CreateIndexesAndFts(conn, log);
        log?.Invoke($"FTS5 题名索引构建完成，耗时 {t0.Elapsed.TotalSeconds:F1} 秒");
        return 0;
    }

    public SearchResult SearchSingle(SearchSpec spec, string keyword, string fmt,
        CancellationToken cancel = default)
    {
        if (!Exists())
            return SingleNoDb();
        using var conn = Db.Open(DbPath);
        return Searcher.SearchOne(conn, spec, keyword, fmt, OutputRoot, cancel);
    }

    public BatchResult SearchBatch(SearchSpec spec, IReadOnlyList<string> keywords, string fmt,
        Action<int, int>? progress = null, CancellationToken cancel = default)
    {
        if (!Exists())
            return BatchNoDb();
        using var conn = Db.Open(DbPath);
        return Searcher.SearchBatch(conn, spec, keywords, fmt, progress, OutputRoot, cancel);
    }

    public BatchResult SearchBatchFromFile(SearchSpec spec, string keywordFile, string fmt,
        Action<int, int>? progress = null, CancellationToken cancel = default)
    {
        if (!Exists())
            return BatchNoDb();
        using var conn = Db.Open(DbPath);
        return Searcher.SearchBatchFromFile(conn, spec, keywordFile, fmt, progress, OutputRoot, cancel);
    }

    private static SearchResult SingleNoDb()
    {
        var r = new SearchResult();
        r.Messages.Add(NoDbMessage);
        r.Error = NoDbMessage;
        return r;
    }

    private static BatchResult BatchNoDb()
    {
        var r = new BatchResult();
        r.Messages.Add(NoDbMessage);
        r.Error = NoDbMessage;
        return r;
    }

    private static void Execute(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        cmd.ExecuteNonQuery();
    }
}
