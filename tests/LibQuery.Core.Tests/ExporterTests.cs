// 导出器测试：文件名清洗、xlsx 截断、预览捕获、csv 内容。
// 移植自 Python 版 tests/test_exporter.py。

using System.Text;
using LibQuery.Core;
using Microsoft.Data.Sqlite;
using Xunit;

namespace LibQuery.Core.Tests;

public sealed class ExporterTests : IDisposable
{
    private readonly string _dir;

    public ExporterTests()
    {
        _dir = Path.Combine(Path.GetTempPath(), "libq-export-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_dir);
    }

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch { /* 清理失败不影响结果 */ }
    }

    private string OutRoot => Path.Combine(_dir, "output");

    private static SqliteConnection MemDbWithRows()
    {
        var conn = Db.Open(":memory:");
        Exec(conn, "CREATE TABLE t(题名 TEXT, 索书号 TEXT)");
        Exec(conn, "INSERT INTO t VALUES ('题名A', 'TP/1'), ('题名B', 'TP/2')");
        return conn;
    }

    private static void Exec(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        cmd.ExecuteNonQuery();
    }

    [Theory]
    [InlineData("a/b:c*?\"<>|", "a-b-c------")]
    [InlineData("正常关键词.xlsx", "正常关键词.xlsx")]
    [InlineData("*", "-")]
    public void CleanName_ReplacesIllegalChars(string input, string expected)
    {
        Assert.Equal(expected, Exporter.CleanName(input));
    }

    [Fact]
    public void CleanName_Truncates()
    {
        Assert.Equal(new string('x', 100), Exporter.CleanName(new string('x', 300)));
    }

    [Fact]
    public void Export_CsvAndPreview()
    {
        using var conn = MemDbWithRows();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT * FROM t";
        using var reader = cmd.ExecuteReader();

        var result = Exporter.ExportRows("csv", "题名", "测试词", ["题名", "索书号"], reader, OutRoot);

        Assert.False(result.Truncated);
        Assert.Equal(2, result.Rows);
        Assert.Equal(Path.Combine(OutRoot, "题名", "测试词.csv"), result.Path);

        var text = File.ReadAllText(result.Path, new UTF8Encoding(false));  // BOM 自动剥离
        var lines = text.Split('\n');
        Assert.Equal("题名,索书号", lines[0].TrimEnd('\r'));
        Assert.Contains("题名A", text);
        // utf-8-sig：文件以 BOM 开头
        var raw = File.ReadAllBytes(result.Path);
        Assert.Equal(0xEF, raw[0]);
        Assert.Equal(0xBB, raw[1]);
        Assert.Equal(0xBF, raw[2]);
    }

    [Fact]
    public void Export_XlsxTruncates()
    {
        var conn = Db.Open(":memory:");
        try
        {
            Exec(conn, "CREATE TABLE t(题名 TEXT)");
            Exec(conn, "INSERT INTO t " + string.Join("\nUNION ALL\n",
                Enumerable.Range(0, 50).Select(i => $"SELECT 'row{i}'")));
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT 题名 FROM t";
            using var reader = cmd.ExecuteReader();

            var result = Exporter.ExportRows("xlsx", "题名", "trunc", ["题名"], reader,
                OutRoot, maxRowsOverride: 5);

            Assert.True(result.Truncated);
            Assert.Equal(5, result.Rows);
            Assert.True(File.Exists(result.Path));
            Assert.Equal(6, CountSheetRows(result.Path));  // 表头 + 5 行
        }
        finally { conn.Dispose(); }
    }

    [Fact]
    public void Export_EmptyResult_KeepsHeader()
    {
        var conn = Db.Open(":memory:");
        try
        {
            Exec(conn, "CREATE TABLE t(题名 TEXT)");
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT 题名 FROM t WHERE 0";
            using var reader = cmd.ExecuteReader();

            var result = Exporter.ExportRows("xlsx", "题名", "empty", ["题名"], reader, OutRoot);

            Assert.Equal(0, result.Rows);
            Assert.False(result.Truncated);
            Assert.Equal(1, CountSheetRows(result.Path));  // 空结果仍有表头行
        }
        finally { conn.Dispose(); }
    }

    [Fact]
    public void FormatPreview_NullAndRows()
    {
        Assert.Null(Exporter.FormatPreview(["A", "B"], []));
        var text = Exporter.FormatPreview(["A", "B"], [new object?[] { "a", null }]);
        Assert.Equal("A | B\na | ", text);
    }

    [Fact]
    public void Export_UnknownFormat_FallsBackToXlsx()
    {
        // Python 版：ext = "csv" if fmt == "csv" else "xlsx"
        using var conn = MemDbWithRows();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT * FROM t";
        using var reader = cmd.ExecuteReader();
        var result = Exporter.ExportRows("whatever", "题名", "fmt", ["题名", "索书号"], reader, OutRoot);
        Assert.EndsWith(".xlsx", result.Path);
    }

    private static int CountSheetRows(string xlsxPath)
    {
        using var stream = File.Open(xlsxPath, FileMode.Open, FileAccess.Read, FileShare.Read);
        using var reader = ExcelDataReader.ExcelReaderFactory.CreateReader(stream);
        int rows = 0;
        while (reader.Read())
            rows++;
        return rows;
    }
}
