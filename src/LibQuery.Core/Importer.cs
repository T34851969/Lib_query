// Excel → SQLite 建库：ExcelDataReader 流式读取、books 表整体重建、索引与 FTS5 trigram 题名索引。
// 移植自 Python 版 lib_query/db/importer.py，行为逐条对齐：
// - 列布局沿用旧版约定：第 1~4 列保持原列名（题名/索书号/标准号等），
//   第 5~11 列按位置重命名为 level_1..level_7；
// - 单元格统一转文本，整数化浮点去掉小数尾巴（Excel 数值格式的 ISBN）；
// - 破坏性重建（先删 FTS 再删 books，顺序敏感）；5000 行分块提交并回报进度。
// 与 Python 版唯一差异：calamine 一次性物化整表，这里改为流式逐块写库
// （内存占用恒定，与本项目"导出恒定内存"同一哲学），进度逐块回报无总数。

using System.Globalization;
using ExcelDataReader;
using Microsoft.Data.Sqlite;

namespace LibQuery.Core;

public sealed record ImportSummary(int Rows, IReadOnlyList<string> Columns, double Seconds);

public static class Importer
{
    public const int ChunkRows = 5000;  // 分批写入，兼顾内存与提交频率

    private static readonly string[] IndexSql =
    {
        "CREATE INDEX IF NOT EXISTS idx_title ON books(\"题名\")",
        "CREATE INDEX IF NOT EXISTS idx_cn_level_1 ON books(\"level_1\")",
        "CREATE INDEX IF NOT EXISTS idx_cn_level_2 ON books(\"level_2\")",
        "CREATE INDEX IF NOT EXISTS idx_cn_level_3 ON books(\"level_3\")",
        "CREATE INDEX IF NOT EXISTS idx_cn_level_4 ON books(\"level_4\")",
        "CREATE INDEX IF NOT EXISTS idx_cn_level_5 ON books(\"level_5\")",
        "CREATE INDEX IF NOT EXISTS idx_cn_level_6 ON books(\"level_6\")",
        "CREATE INDEX IF NOT EXISTS idx_cn_level_7 ON books(\"level_7\")",
        "CREATE INDEX IF NOT EXISTS idx_call_number ON books(\"索书号\")",
        "CREATE INDEX IF NOT EXISTS idx_ISBN ON books(\"标准号\")",
    };

    private const string FtsDdl =
        "CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(" +
        "\"题名\", content='books', content_rowid='rowid', tokenize='trigram')";

    private static readonly string[] TriggerSql =
    {
        """
        CREATE TRIGGER IF NOT EXISTS books_fts_ai AFTER INSERT ON books BEGIN
            INSERT INTO books_fts(rowid, "题名") VALUES (new.rowid, new."题名");
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS books_fts_ad AFTER DELETE ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, "题名") VALUES ('delete', old.rowid, old."题名");
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS books_fts_au AFTER UPDATE OF "题名" ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, "题名") VALUES ('delete', old.rowid, old."题名");
            INSERT INTO books_fts(rowid, "题名") VALUES (new.rowid, new."题名");
        END
        """,
    };

    /// <summary>单元格统一转文本；整数化浮点去掉小数尾巴（如 Excel 数值格式的 ISBN）。</summary>
    public static string? ToStr(object? value)
    {
        if (value is null or DBNull)
            return null;
        if (value is double d && double.IsFinite(d) && d == Math.Floor(d) && Math.Abs(d) < 1e15)
            return ((long)d).ToString(CultureInfo.InvariantCulture);
        if (value is DateTime dt)
            return dt.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
        return Convert.ToString(value, CultureInfo.InvariantCulture);
    }

    private static void Execute(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        cmd.ExecuteNonQuery();
    }

    /// <summary>
    /// 在 books 表上建立常规索引与 FTS5 外部内容索引（幂等，可对存量库调用）。
    /// 对应 Python 版 create_indexes_and_fts。
    /// </summary>
    public static void CreateIndexesAndFts(SqliteConnection conn, Action<string>? progress = null)
    {
        foreach (var sql in IndexSql)
            Execute(conn, sql);
        Execute(conn, FtsDdl);
        foreach (var ddl in TriggerSql)
            Execute(conn, ddl);
        progress?.Invoke("正在构建 FTS5 题名索引（大库约需 1~2 分钟）...");
        Execute(conn, "INSERT INTO books_fts(books_fts) VALUES('rebuild')");
    }

    /// <summary>
    /// 读取 Excel 首个工作表，整体重建 books 表并建立索引/FTS。
    /// 返回 (行数, 列名, 秒数)。该操作为破坏性重建（先删后建）。
    /// </summary>
    public static ImportSummary ImportExcel(string excelFile, string dbPath, Action<string>? progress = null)
    {
        var t0 = System.Diagnostics.Stopwatch.StartNew();

        // 首个工作表流式读取（xlsx=SAX，大表内存恒定；表头行为首行，与 calamine 首表语义一致）
        using var stream = File.Open(excelFile, FileMode.Open, FileAccess.Read, FileShare.Read);
        using var reader = ExcelReaderFactory.CreateReader(stream);
        if (!reader.Read())
            throw new InvalidDataException("Excel 首个工作表为空");

        int width = reader.FieldCount;
        var header = new string[width];
        for (int c = 0; c < width; c++)
        {
            var cell = Convert.ToString(reader.GetValue(c), CultureInfo.InvariantCulture);
            header[c] = cell?.Trim() ?? "";
        }
        for (int i = 4; i < Math.Min(11, width); i++)
            header[i] = $"level_{i - 3}";

        // 表头行已消费；再前进一行才是首条数据（仅表头的空数据表 → 不插入任何行）
        bool more = reader.Read();

        var conn = Db.Open(dbPath);
        try
        {
            // 顺序敏感：先删 FTS（外部内容表悬空会报错），再删内容表
            Execute(conn, "DROP TABLE IF EXISTS books_fts");
            Execute(conn, "DROP TABLE IF EXISTS books");
            var colsSql = string.Join(", ", header.Select(c => $"\"{c}\" TEXT"));
            Execute(conn, $"CREATE TABLE books ({colsSql})");

            var placeholders = string.Join(", ", header.Select((_, i) => $"@p{i}"));
            using var insert = conn.CreateCommand();
            insert.CommandText = $"INSERT INTO books VALUES ({placeholders})";
            for (int i = 0; i < width; i++)
                insert.Parameters.Add($"@p{i}", SqliteType.Text);

            long inserted = 0;
            while (more)
            {
                using var tx = conn.BeginTransaction();
                insert.Transaction = tx;
                for (int chunk = 0; chunk < ChunkRows && more; chunk++)
                {
                    for (int i = 0; i < width; i++)
                        insert.Parameters[i].Value = (object?)ToStr(reader.GetValue(i)) ?? DBNull.Value;
                    insert.ExecuteNonQuery();
                    inserted++;
                    more = reader.Read();
                }
                tx.Commit();
                progress?.Invoke($"已写入 {inserted} 行");
            }

            CreateIndexesAndFts(conn, progress);

            return new ImportSummary((int)inserted, header, Math.Round(t0.Elapsed.TotalSeconds, 1));
        }
        finally
        {
            conn.Dispose();
        }
    }
}
