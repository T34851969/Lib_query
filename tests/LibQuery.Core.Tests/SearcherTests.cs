// 检索实现测试：四种模式、FTS 索引路径、回退路径、单次与批量、取消。
// 移植自 Python 版 tests/test_search.py，断言计数沿用旧版规律。

using LibQuery.Core;
using Microsoft.Data.Sqlite;
using Xunit;

namespace LibQuery.Core.Tests;

public sealed class SearcherTests : IDisposable
{
    private static readonly SearchSpec TitleSpec =
        new("title", "题名", "题名检索", Searcher.ModeTitle);
    private static readonly SearchSpec IsbnSpec =
        new("isbn", "ISBN", "ISBN检索", Searcher.ModeExact, Column: "标准号");
    private static readonly SearchSpec CallNumSpec =
        new("call_num", "索书号", "索书号检索", Searcher.ModeExact, Column: "索书号");
    private static readonly SearchSpec PieceSpec =
        new("call_num_piece", "索书号切片", "索书号切片检索", Searcher.ModePiece);

    private readonly string _dir;

    public SearcherTests()
    {
        _dir = Path.Combine(Path.GetTempPath(), "libq-tests-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_dir);
    }

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch { /* 清理失败不影响结果 */ }
    }

    private string OutRoot => Path.Combine(_dir, "output");

    private LibraryService MakeService(int n = 200, bool withFts = true)
    {
        var db = Path.Combine(_dir, "synth.db");
        SynthDb.MakeBooksDb(db, n, withFts);
        return new LibraryService(db, OutRoot);
    }

    private static List<string> ExplainPlan(SqliteConnection conn, string sql, List<object> parameters)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "EXPLAIN QUERY PLAN " + sql;
        for (int i = 0; i < parameters.Count; i++)
            cmd.Parameters.AddWithValue($"@p{i}", parameters[i]);
        var details = new List<string>();
        using var r = cmd.ExecuteReader();
        while (r.Read())
            details.Add(r.IsDBNull(3) ? "" : r.GetString(3));
        return details;
    }

    [Fact]
    public void TitleQuery_UsesFtsIndex()
    {
        using var conn = Db.Open(SynthDb.MakeBooksDb(Path.Combine(_dir, "fts.db")));
        var (sql, parameters, notes) = Searcher.BuildQuery(conn, TitleSpec, "计算机网络");
        Assert.Empty(notes);
        var plan = string.Join("\n", ExplainPlan(conn, sql, parameters));
        // M1 = FTS 虚表按 MATCH 约束走索引，而非全表扫描
        Assert.Contains("VIRTUAL TABLE INDEX 0:M1", plan);
    }

    [Fact]
    public void TitleShortKeyword_FallsBackToLike()
    {
        using var conn = Db.Open(SynthDb.MakeBooksDb(Path.Combine(_dir, "fts2.db")));
        var (sql, parameters, _) = Searcher.BuildQuery(conn, TitleSpec, "数");
        Assert.Contains("LIKE", sql);
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        cmd.Parameters.AddWithValue("@p0", parameters[0]);
        var count = 0;
        using (var r = cmd.ExecuteReader())
            while (r.Read())
                count++;
        Assert.True(count > 0);
    }

    [Fact]
    public void TitleWithoutFts_WarnsAndFallsBack()
    {
        var db = Path.Combine(_dir, "nofts.db");
        SynthDb.MakeBooksDb(db, 50, withFts: false);
        using var conn = Db.Open(db);
        var (sql, _, notes) = Searcher.BuildQuery(conn, TitleSpec, "计算机网络");
        Assert.Contains("LIKE", sql);
        Assert.Contains(notes, n => n.Contains("--rebuild-fts"));
    }

    [Fact]
    public void TitleSearch_FindsSeededRows()
    {
        var service = MakeService();
        var result = service.SearchSingle(TitleSpec, "计算机网络", "csv");
        Assert.Null(result.Error);
        Assert.Equal(25, result.Rows);  // 8 种题名循环 200 行，含该词的题名占 1/8
        Assert.NotNull(result.Preview);
        Assert.Contains("计算机网络", result.Preview!);
        Assert.True(File.Exists(Path.Combine(OutRoot, "题名", "计算机网络.csv")));
    }

    [Fact]
    public void TitleSearch_FtsPhraseWithQuotes()
    {
        // 关键词含双引号时不 crash，且短语转义正确
        var service = MakeService();
        var result = service.SearchSingle(TitleSpec, "导\"论", "csv");
        Assert.Null(result.Error);
    }

    [Fact]
    public void IsbnExactSearch()
    {
        var service = MakeService();
        var result = service.SearchSingle(IsbnSpec, "9787000000005", "csv");
        Assert.Equal(1, result.Rows);
        Assert.Contains("9787000000005", result.Preview!);
    }

    [Fact]
    public void CallNumExactSearch()
    {
        var service = MakeService();
        var result = service.SearchSingle(CallNumSpec, "TP311.13/1", "csv");
        Assert.Equal(1, result.Rows);
    }

    [Fact]
    public void PieceSearch()
    {
        var service = MakeService();
        // 'I247'（4 位）→ level_4 等值匹配
        var result = service.SearchSingle(PieceSpec, "I247", "csv");
        Assert.Equal(50, result.Rows);  // 200 行中每 4 行一个分类
        // 'I247.5'（6 位）→ level_5 等值匹配（len>5 时 idx-1=5）
        var result2 = service.SearchSingle(PieceSpec, "I247.5", "csv");
        Assert.Equal(50, result2.Rows);
    }

    [Fact]
    public void SingleEmptyKeyword()
    {
        var service = MakeService();
        var result = service.SearchSingle(TitleSpec, "   ", "csv");
        Assert.Contains("非法输入", result.Messages[0]);
    }

    [Fact]
    public void SingleWithoutDb()
    {
        var service = new LibraryService(Path.Combine(_dir, "missing.db"), OutRoot);
        var result = service.SearchSingle(TitleSpec, "x", "csv");
        Assert.Contains("数据库不存在", result.Error!);
    }

    [Fact]
    public void BatchWrites_OneFilePerKeyword()
    {
        var service = MakeService();
        var progressLog = new List<(int Done, int Total)>();
        var result = service.SearchBatch(
            IsbnSpec, ["9787000000000", "9787000000001", ""], "csv",
            progress: (done, total) => progressLog.Add((done, total)));
        Assert.Null(result.Error);
        Assert.Equal(2, result.Items.Count);  // 空关键词被过滤
        Assert.Equal([(1, 2), (2, 2)], progressLog);
        Assert.True(File.Exists(Path.Combine(OutRoot, "ISBN", "9787000000000.csv")));
        Assert.True(File.Exists(Path.Combine(OutRoot, "ISBN", "9787000000001.csv")));
    }

    [Fact]
    public void BatchFrom_File()
    {
        var service = MakeService();
        var keyFile = Path.Combine(_dir, "keys.txt");
        File.WriteAllLines(keyFile, ["9787000000000", "", "9787000000001"]);
        var result = service.SearchBatchFromFile(IsbnSpec, keyFile, "csv");
        Assert.Null(result.Error);
        Assert.Equal(2, result.Items.Count);
    }

    [Fact]
    public void BatchFromFile_EmptyFile()
    {
        var service = MakeService();
        var keyFile = Path.Combine(_dir, "empty.txt");
        File.WriteAllLines(keyFile, ["", "  "]);
        var result = service.SearchBatchFromFile(IsbnSpec, keyFile, "csv");
        Assert.NotNull(result.Error);
        Assert.Contains("文件中无有效内容", result.Messages);
    }

    [Fact]
    public void BatchEmptyList()
    {
        var service = MakeService();
        var result = service.SearchBatch(IsbnSpec, ["", "  "], "csv");
        Assert.Contains("无有效关键词", result.Messages);
        Assert.NotNull(result.Error);
    }

    [Fact]
    public void BatchCancel_Preset()
    {
        var service = MakeService();
        using var cts = new CancellationTokenSource();
        cts.Cancel();  // 预先置位：立即取消
        var result = service.SearchBatch(IsbnSpec, ["9787000000000", "9787000000001"], "csv",
            cancel: cts.Token);
        Assert.True(result.Cancelled);
        Assert.Empty(result.Items);
    }

    [Fact]
    public void SearchCancel_DuringExport()
    {
        // 导出中途取消：半成品文件被清理（对齐 Python 版 test_search_cancel_during_export）
        var db = Path.Combine(_dir, "big.db");
        SynthDb.MakeBooksDb(db, 20000, withFts: false);
        using var conn = Db.Open(db);
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT 题名 FROM books";
        using var reader = cmd.ExecuteReader();
        using var cts = new CancellationTokenSource();
        cts.Cancel();

        var ex = Assert.Throws<ExportCancelled>(() =>
            Exporter.ExportRows("csv", "题名", "cancel-test", ["题名"], reader,
                OutRoot, cts.Token, checkEvery: 1000));
        Assert.Contains("导出已取消", ex.Message);
        Assert.False(File.Exists(Path.Combine(OutRoot, "题名", "cancel-test.csv")));
    }
}
