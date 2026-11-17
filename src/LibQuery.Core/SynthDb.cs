// 合成馆藏数据库生成器（tests / bench / 自检共用）。
// 构造可预测的数据：索书号分段规律、题名/ISBN 覆盖各检索路径；
// 与 Python 版 tests/conftest.py 的 _synth_rows 规律一致（断言计数沿用旧版）。

using System.Globalization;
using Microsoft.Data.Sqlite;

namespace LibQuery.Core;

public static class SynthDb
{
    public static readonly string[] Classes = { "TP311.13", "I247.5", "O13", "K207" };

    public static readonly string[] Titles =
    {
        "数据结构教程", "计算机网络自顶向下", "操作系统导论", "数据库系统原理",
        "机器学习实战", "中国通史纲要", "高等数学（第二版）", "西方经济学",
    };

    public static readonly string[] Columns =
        ["题名", "索书号", "标准号", "出版年", "level_1", "level_2", "level_3", "level_4", "level_5", "level_6", "level_7"];

    /// <summary>Python 切片语义的前缀（超长钳制，对应 cls[:n]）。</summary>
    private static string Prefix(string s, int len) => s.Length <= len ? s : s[..len];

    /// <summary>第 i 行的取值（与 MakeBooksDb 完全一致，供 bench 逐行产出使用）。</summary>
    public static string[] RowValues(int i)
    {
        var cls = Classes[i % Classes.Length];
        var title = $"{Titles[i % Titles.Length]}·第{i % 40 + 1}册";
        var call = $"{cls}/{i + 1}";
        var isbn = "9787" + i.ToString("D9", CultureInfo.InvariantCulture);
        var year = (1980 + i % 45).ToString(CultureInfo.InvariantCulture);
        return
        [
            title, call, isbn, year,
            Prefix(cls, 1), Prefix(cls, 2), Prefix(cls, 3), Prefix(cls, 4), cls,
            call.Split('/')[0], call,
        ];
    }

    /// <summary>构造与正式库同构的合成库（books + 索引 + FTS5 trigram）。</summary>
    public static string MakeBooksDb(string path, int n = 200, bool withFts = true)
    {
        var conn = Db.Open(path);
        try
        {
            Exec(conn, $"CREATE TABLE books ({string.Join(", ", Columns.Select(c => $"\"{c}\" TEXT"))})");
            using var tx = conn.BeginTransaction();
            using var cmd = conn.CreateCommand();
            cmd.Transaction = tx;
            cmd.CommandText =
                $"INSERT INTO books VALUES ({string.Join(", ", Columns.Select((_, i) => $"@p{i}"))})";
            for (int i = 0; i < Columns.Length; i++)
                cmd.Parameters.Add($"@p{i}", SqliteType.Text);
            for (int i = 0; i < n; i++)
            {
                var vals = RowValues(i);
                for (int c = 0; c < vals.Length; c++)
                    cmd.Parameters[c].Value = vals[c];
                cmd.ExecuteNonQuery();
            }
            tx.Commit();
            if (withFts)
                Importer.CreateIndexesAndFts(conn);
        }
        finally
        {
            conn.Dispose();
        }
        return path;
    }

    private static void Exec(SqliteConnection conn, string sql)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        cmd.ExecuteNonQuery();
    }
}
