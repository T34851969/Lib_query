// 数据库连接、路径与能力检查。移植自 Python 版 lib_query/db/core.py：
// - 每次任务新建连接、用完即关（检索/导入均为工作线程调用，互不共享连接）；
// - PRAGMA 与 Python 版一致（cache_size=100000 页 + 内存临时表）；
// - FTS5 trigram 能力探测（Microsoft.Data.Sqlite 内嵌 e_sqlite3，自带 FTS5）。

using Microsoft.Data.Sqlite;

namespace LibQuery.Core;

public static class Db
{
    /// <summary>FTS5 trigram tokenizer 的最低 SQLite 版本（3.34）。</summary>
    public static readonly Version RequiredSqliteMin = new(3, 34);

    public static SqliteConnection Open(string path)
    {
        var conn = new SqliteConnection(new SqliteConnectionStringBuilder
        {
            DataSource = path,
            Pooling = false,
        }.ToString());
        conn.Open();
        ExecutePragma(conn, "PRAGMA cache_size = 100000");
        ExecutePragma(conn, "PRAGMA temp_store = MEMORY");
        return conn;
    }

    private static void ExecutePragma(SqliteConnection conn, string pragma)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = pragma;
        cmd.ExecuteNonQuery();
    }

    /// <summary>当前内嵌 SQLite 是否支持 FTS5 及 trigram 分词器。</summary>
    public static bool SupportsFtsTrigram()
    {
        var conn = new SqliteConnection("Data Source=:memory:");
        try
        {
            conn.Open();
            var version = new Version(conn.ServerVersion);
            if (version < RequiredSqliteMin)
                return false;
            ExecutePragma(conn,
                "CREATE VIRTUAL TABLE _probe USING fts5(x, tokenize='trigram')");
            return true;
        }
        catch (SqliteException)
        {
            return false;
        }
        finally
        {
            conn.Dispose();
        }
    }

    /// <summary>表或视图是否存在（对应 Python 版 table_exists，books_fts 是虚表）。</summary>
    public static bool TableExists(SqliteConnection conn, string name)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText =
            "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = @name";
        cmd.Parameters.AddWithValue("@name", name);
        return cmd.ExecuteScalar() is not null;
    }
}
