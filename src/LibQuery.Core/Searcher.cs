// 参数化检索实现：一套模板覆盖 题名/索书号/索书号切片/ISBN 四种检索。
// 移植自 Python 版 lib_query/db/search.py，SQL 与行为逐条对齐：
// - 索书号切片定位规则：长度 >5 的切片按 level_(len-1) 精确匹配；5 位切片在 level_5 前缀匹配；
// - 题名 ≥3 字符走 FTS5 trigram 短语查询，缺索引或更短关键词回退 LIKE 全表扫描；
// - LIKE 统一 ESCAPE '\'，转义 \ % _；FTS 短语双引号翻倍；
// - 每个关键词独立导出一个文件，单关键词失败不影响批量其余关键词。

using Microsoft.Data.Sqlite;

namespace LibQuery.Core;

public sealed record SearchSpec(
    string Key, string DirName, string Label, string Mode, string Column = "", string Tip = "");

public sealed class SearchResult
{
    public string Keyword { get; set; } = "";
    public List<string> Messages { get; } = new();
    public string? Preview { get; set; }
    public string? OutputFile { get; set; }
    public int Rows { get; set; }
    public bool Cancelled { get; set; }
    public string? Error { get; set; }
}

public sealed class BatchResult
{
    public List<string> Messages { get; } = new();
    public List<SearchResult> Items { get; } = new();
    public bool Cancelled { get; set; }
    public string? Error { get; set; }
}

public static class Searcher
{
    public const string ModeExact = "exact";   // 等值匹配（索书号 / ISBN）
    public const string ModePiece = "piece";   // 索书号切片：按关键词长度定位 level_N 列
    public const string ModeTitle = "title";   // 题名模糊检索：FTS5 trigram，缺失时回退 LIKE

    /// <summary>单条 LIKE 导出过程中每 5000 行检查一次取消。</summary>
    public const int CancelCheckEvery = 5000;

    // 题名回退查询（FTS 不可用或关键词不足 3 字符时）；统一位置参数命名 @p0
    private const string LikeTitleSql =
        "SELECT * FROM books WHERE \"题名\" LIKE @p0 ESCAPE '\\'";

    public static string EscapeLike(string word) =>
        word.Replace("\\", "\\\\").Replace("%", "\\%").Replace("_", "\\_");

    /// <summary>包装为 FTS5 短语查询，双引号翻倍转义，其余字符按字面处理。</summary>
    public static string QuoteFtsPhrase(string word) => "\"" + word.Replace("\"", "\"\"") + "\"";

    /// <summary>构造 (sql, 参数, 附加提示)。对应 Python 版 build_query。</summary>
    public static (string Sql, List<object> Params, List<string> Notes) BuildQuery(
        SqliteConnection conn, SearchSpec spec, string keyword)
    {
        var kw = keyword.Trim();
        if (spec.Mode == ModeExact)
        {
            var sql = $"SELECT * FROM books WHERE \"{spec.Column}\" = @p0";
            return (sql, [kw], []);
        }

        if (spec.Mode == ModePiece)
        {
            // 沿用旧版定位规则：长度 >5 的切片按 level_(len-1) 精确匹配；
            // 5 位切片在 level_5 上做前缀匹配
            var idx = kw.Length;
            if (idx > 5)
                idx -= 1;
            var col = $"level_{idx}";
            if (col == "level_5" && kw.Length == 5)
            {
                const string prefixSql = "SELECT * FROM books WHERE \"level_5\" LIKE @p0 ESCAPE '\\'";
                return (prefixSql, [EscapeLike(kw) + "%"], []);
            }
            var sql = $"SELECT * FROM books WHERE \"{col}\" = @p0";
            return (sql, [kw], []);
        }

        if (spec.Mode == ModeTitle)
        {
            var notes = new List<string>();
            if (kw.Length >= 3)
            {
                if (Db.TableExists(conn, "books_fts"))
                {
                    const string ftsSql =
                        "SELECT b.* FROM books b JOIN books_fts f ON f.rowid = b.rowid " +
                        "WHERE books_fts MATCH @p0";
                    return (ftsSql, [QuoteFtsPhrase(kw)], notes);
                }
                notes.Add("提示：未检测到 books_fts 索引，题名检索回退全表扫描" +
                          "（可运行 LibQuery.exe --rebuild-fts 补建索引）");
            }
            return (LikeTitleSql, ["%" + EscapeLike(kw) + "%"], notes);
        }

        throw new ArgumentException($"未知检索模式: {spec.Mode}");
    }

    /// <summary>单关键词检索 + 流式导出，返回结构化结果（异常在内部捕获）。</summary>
    public static SearchResult SearchOne(
        SqliteConnection conn, SearchSpec spec, string keyword, string fmt,
        string? outRoot = null, CancellationToken cancel = default,
        int checkEvery = CancelCheckEvery)
    {
        var result = new SearchResult { Keyword = keyword.Trim() };
        var kw = keyword.Trim();
        if (kw.Length == 0)
        {
            result.Messages.Add("非法输入（空关键词）");
            return result;
        }

        try
        {
            var (sql, parameters, notes) = BuildQuery(conn, spec, kw);
            result.Messages.AddRange(notes);
            result.Messages.Add($"搜索: {kw}");

            using var cmd = conn.CreateCommand();
            cmd.CommandText = sql;
            for (int i = 0; i < parameters.Count; i++)
                cmd.Parameters.AddWithValue($"@p{i}", parameters[i] ?? DBNull.Value);

            using var reader = cmd.ExecuteReader();
            var columns = Enumerable.Range(0, reader.FieldCount)
                .Select(reader.GetName).ToList();

            var export = Exporter.ExportRows(fmt, spec.DirName, kw, columns, reader,
                outRoot, cancel, checkEvery);

            result.Rows = export.Rows;
            result.OutputFile = export.Path;
            if (export.Truncated)
                result.Messages.Add($"警告：结果超出 Excel 单表行数上限，已截断为 {export.Rows} 行");
            result.Messages.Add($"搜索完成！找到 {export.Rows} 条记录");
            result.Messages.Add($"结果已保存到: {export.Path}");
            result.Preview = Exporter.FormatPreview(columns, export.Head);
            return result;
        }
        catch (ExportCancelled)
        {
            result.Cancelled = true;
            result.Messages.Add("已取消（部分结果未保存）");
            return result;
        }
        catch (Exception err)  // 单关键词失败不影响批量中的其余关键词
        {
            result.Error = err.Message;
            result.Messages.Add($"搜索失败: {err.Message}");
            return result;
        }
    }

    /// <summary>批量检索（关键词列表）：每个关键词一次索引查询 + 独立导出一个文件。</summary>
    public static BatchResult SearchBatch(
        SqliteConnection conn, SearchSpec spec, IReadOnlyList<string> keywords, string fmt,
        Action<int, int>? progress = null, string? outRoot = null,
        CancellationToken cancel = default)
    {
        var result = new BatchResult();
        var kws = keywords
            .Select(k => (k ?? "").Trim())
            .Where(k => k.Length > 0)
            .ToList();
        if (kws.Count == 0)
        {
            result.Messages.Add("无有效关键词");
            result.Error = "无有效输入";
            return result;
        }
        result.Messages.Add($"加载 {kws.Count} 个 {spec.Label} 关键词");
        RunBatch(conn, spec, kws, fmt, result, progress, outRoot, cancel);
        return result;
    }

    /// <summary>批量检索（TXT 文件，utf-8-sig）：每行一个关键词。</summary>
    public static BatchResult SearchBatchFromFile(
        SqliteConnection conn, SearchSpec spec, string filePath, string fmt,
        Action<int, int>? progress = null, string? outRoot = null,
        CancellationToken cancel = default)
    {
        var result = new BatchResult();
        string[] lines;
        try
        {
            lines = File.ReadAllLines(filePath);  // StreamReader 默认检测并剥离 BOM
        }
        catch (Exception err)
        {
            result.Messages.Add($"读取文件时出错: {err.Message}");
            result.Error = "无有效输入";
            return result;
        }
        var kws = lines
            .Select(k => k.Trim())
            .Where(k => k.Length > 0)
            .ToList();
        if (kws.Count == 0)
        {
            result.Messages.Add("文件中无有效内容");
            result.Error = "无有效输入";
            return result;
        }
        result.Messages.Add($"加载 {kws.Count} 个 {spec.Label} 关键词");
        RunBatch(conn, spec, kws, fmt, result, progress, outRoot, cancel);
        return result;
    }

    private static void RunBatch(
        SqliteConnection conn, SearchSpec spec, List<string> kws, string fmt,
        BatchResult result, Action<int, int>? progress, string? outRoot,
        CancellationToken cancel)
    {
        int total = kws.Count;
        for (int i = 0; i < total; i++)
        {
            if (cancel.IsCancellationRequested)
            {
                result.Cancelled = true;
                result.Messages.Add($"已取消：完成 {i}/{total} 个关键词");
                return;
            }
            var item = SearchOne(conn, spec, kws[i], fmt, outRoot, cancel);
            result.Items.Add(item);
            if (item.Cancelled)
            {
                result.Cancelled = true;
                result.Messages.Add($"已取消：完成 {i + 1}/{total} 个关键词");
                return;
            }
            progress?.Invoke(i + 1, total);
        }
    }
}
