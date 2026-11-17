// 导入器测试：ExcelDataReader 读取、列重命名、类型规整、FTS 构建、破坏性重建。
// 移植自 Python 版 tests/test_importer.py。

using System.IO.Compression;
using System.Text;
using LibQuery.Core;
using Microsoft.Data.Sqlite;
using MiniExcelLibs;
using Xunit;

namespace LibQuery.Core.Tests;

public sealed class ImporterTests : IDisposable
{
    private readonly string _dir;

    public ImporterTests()
    {
        _dir = Path.Combine(Path.GetTempPath(), "libq-import-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_dir);
    }

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch { /* 清理失败不影响结果 */ }
    }

    /// <summary>构造与馆藏格式一致的 Excel：前 4 列保留原名，后 7 列将被按位置重命名。</summary>
    private string MakeSampleExcel(string name = "馆藏.xlsx")
    {
        var path = Path.Combine(_dir, name);
        // 字典行保留逐格类型：第 3 行 标准号 为数值（Excel 中未按文本存储的典型情况）
        var rows = new List<Dictionary<string, object?>>
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
        MiniExcel.SaveAs(path, rows);
        return path;
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

    private static string Text(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        return Convert.ToString(cmd.ExecuteScalar()) ?? "";
    }

    [Fact]
    public void Import_RebuildsBooksAndFts()
    {
        var sample = MakeSampleExcel();
        var db = Path.Combine(_dir, "imported.db");
        var messages = new List<string>();
        var summary = Importer.ImportExcel(sample, db, messages.Add);

        Assert.Equal(3, summary.Rows);
        Assert.Equal("level_1", summary.Columns[4]);
        Assert.Equal("level_7", summary.Columns[10]);
        Assert.Contains(messages, m => m.Contains("FTS5"));

        using var conn = Db.Open(db);
        var cols = new List<string>();
        using (var cmd = conn.CreateCommand())
        {
            cmd.CommandText = "PRAGMA table_info(books)";
            using var r = cmd.ExecuteReader();
            while (r.Read())
                cols.Add(r.GetString(1));
        }
        Assert.Equal(Enumerable.Range(1, 7).Select(i => $"level_{i}"), cols.Skip(4));
        Assert.Equal(3, Scalar(conn, "SELECT COUNT(*) FROM books"));

        // 数值 ISBN 被规整为无小数尾巴的文本
        Assert.Equal("9787111544937",
            Text(conn, "SELECT \"标准号\" FROM books WHERE \"题名\" = '操作系统导论'"));

        // FTS 索引可查
        Assert.Equal(1,
            Scalar(conn, "SELECT COUNT(*) FROM books_fts WHERE books_fts MATCH '\"数据结构\"'"));
    }

    [Fact]
    public void Import_IsDestructiveRebuild()
    {
        // 重复导入不残留旧数据/旧索引
        var sample = MakeSampleExcel("馆藏2.xlsx");
        var db = Path.Combine(_dir, "reimport.db");
        Importer.ImportExcel(sample, db);
        Importer.ImportExcel(sample, db);
        using var conn = Db.Open(db);
        Assert.Equal(3, Scalar(conn, "SELECT COUNT(*) FROM books"));
        Assert.Equal(3, Scalar(conn, "SELECT COUNT(*) FROM books_fts"));
    }

    [Fact]
    public void Import_EmptySheet_Throws()
    {
        var path = Path.Combine(_dir, "empty.xlsx");
        MakeEmptyXlsx(path);
        Assert.Throws<InvalidDataException>(
            () => Importer.ImportExcel(path, Path.Combine(_dir, "x.db")));
    }

    [Fact]
    public void ToStr_NormalizesCells()
    {
        Assert.Null(Importer.ToStr(null));
        Assert.Null(Importer.ToStr(DBNull.Value));
        Assert.Equal("9787111544937", Importer.ToStr(9787111544937d));   // 整数化浮点去尾差
        Assert.Equal("12.5", Importer.ToStr(12.5d));
        Assert.Equal("true_text", Importer.ToStr("true_text"));
    }

    [Fact]
    public void RebuildFts_OnLegacyDb()
    {
        // 存量库（无 FTS）一键补建：对应 Python 版 scripts/rebuild_fts.py
        var db = Path.Combine(_dir, "legacy.db");
        SynthDb.MakeBooksDb(db, 60, withFts: false);
        Assert.Equal(0, LibraryService.RebuildFts(db, force: false, log: null));
        using var conn = Db.Open(db);
        Assert.Equal(1,
            Scalar(conn, "SELECT COUNT(*) FROM sqlite_master WHERE name = 'books_fts'"));
        Assert.Equal(60, Scalar(conn, "SELECT COUNT(*) FROM books_fts"));

        // 幂等：再次调用不报错也不重建
        Assert.Equal(0, LibraryService.RebuildFts(db, force: false, log: null));
    }

    /// <summary>构造只有一个空白工作表的 xlsx（对应 xlsxwriter wb.add_worksheet() 的空表）。</summary>
    private static void MakeEmptyXlsx(string path)
    {
        const string contentTypes =
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">" +
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>" +
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>" +
            "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>" +
            "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>" +
            "</Types>";
        const string rels =
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">" +
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>" +
            "</Relationships>";
        const string workbook =
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
            "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" " +
            "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">" +
            "<sheets><sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>";
        const string workbookRels =
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">" +
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>" +
            "</Relationships>";
        const string sheet =
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData/></worksheet>";

        using var fs = File.Create(path);
        using var zip = new ZipArchive(fs, ZipArchiveMode.Create);
        void Entry(string name, string content)
        {
            var entry = zip.CreateEntry(name);
            using var writer = new StreamWriter(entry.Open(), new UTF8Encoding(false));
            writer.Write(content);
        }
        Entry("[Content_Types].xml", contentTypes);
        Entry("_rels/.rels", rels);
        Entry("xl/workbook.xml", workbook);
        Entry("xl/_rels/workbook.xml.rels", workbookRels);
        Entry("xl/worksheets/sheet1.xml", sheet);
    }
}
