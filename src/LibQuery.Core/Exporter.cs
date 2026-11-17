// 结果流式导出：SQLite 游标逐行写出 xlsx/csv，内存占用恒定。
// 移植自 Python 版 lib_query/db/exporter.py，行为逐条对齐：
// - xlsx 走 MiniExcel 的 DataReader 流式通道（表头取自游标列名，空结果也有表头）；
// - csv 为 utf-8-sig + \r\n + QUOTE_MINIMAL 语义，与 Python csv.writer 一致；
// - 写入过程中支持取消：取消时删除半成品文件并抛 ExportCancelled；
// - xlsx 截断于 1,048,575 数据行（Excel 单表上限），csv 不截断；
// - 前 5 行留作界面预览（HeadCapture）。

using System.Collections;
using System.Data;
using System.Data.Common;
using System.Globalization;
using System.Text;
using MiniExcelLibs;

namespace LibQuery.Core;

/// <summary>导出过程被用户取消。</summary>
public sealed class ExportCancelled : Exception
{
    public ExportCancelled(string message) : base(message) { }
}

public sealed record ExportResult(
    string Path, int Rows, bool Truncated, IReadOnlyList<object?[]> Head);

/// <summary>
/// 包装 DbDataReader：留前 N 行预览、计数、xlsx 行数截断、按行数间隔检查取消。
/// 释放本包装不释放内层 reader（内层由调用方管理生命周期）。
/// </summary>
public sealed class CancellableReader : DbDataReader
{
    private readonly DbDataReader _inner;
    private readonly CancellationToken _cancel;
    private readonly int _checkEvery;
    private readonly int _maxRows;
    private bool _done;

    public List<object?[]> Head { get; } = new();
    public int HeadLimit { get; }
    public int RowsRead { get; private set; }
    public bool Truncated { get; private set; }

    public CancellableReader(DbDataReader inner, int headLimit = 5,
        CancellationToken cancel = default, int checkEvery = 5000, int maxRows = int.MaxValue)
    {
        _inner = inner;
        HeadLimit = headLimit;
        _cancel = cancel;
        _checkEvery = checkEvery;
        _maxRows = maxRows;
    }

    public override bool Read()
    {
        if (_done)
            return false;
        if (RowsRead >= _maxRows)
        {
            Truncated = true;   // 已写满 maxRows 行，第 maxRows+1 行起丢弃（对齐 Python：先写满后判）
            _done = true;
            return false;
        }
        if (!_inner.Read())
        {
            _done = true;
            return false;
        }
        RowsRead++;
        if (Head.Count < HeadLimit)
        {
            var row = new object?[FieldCount];
            for (int c = 0; c < FieldCount; c++)
                row[c] = _inner.IsDBNull(c) ? null : _inner.GetValue(c);
            Head.Add(row);
        }
        if (_cancel.CanBeCanceled && RowsRead % _checkEvery == 0 && _cancel.IsCancellationRequested)
            throw new ExportCancelled($"导出已取消（已处理 {RowsRead} 行）");
        return true;
    }

    public override bool IsDBNull(int ordinal) => _inner.IsDBNull(ordinal);
    public override object GetValue(int ordinal) => _inner.GetValue(ordinal);
    public override int FieldCount => _inner.FieldCount;
    public override string GetName(int ordinal) => _inner.GetName(ordinal);
    public override string GetDataTypeName(int ordinal) => _inner.GetDataTypeName(ordinal);
    public override Type GetFieldType(int ordinal) => _inner.GetFieldType(ordinal);
    public override int GetOrdinal(string name) => _inner.GetOrdinal(name);
    public override bool HasRows => _inner.HasRows;
    public override bool IsClosed => _inner.IsClosed;
    public override int RecordsAffected => _inner.RecordsAffected;
    public override int Depth => _inner.Depth;
    public override object this[int ordinal] => _inner[ordinal];
    public override object this[string name] => _inner[name];
    public override bool GetBoolean(int ordinal) => _inner.GetBoolean(ordinal);
    public override byte GetByte(int ordinal) => _inner.GetByte(ordinal);
    public override long GetBytes(int ordinal, long dataOffset, byte[]? buffer, int bufferOffset, int length)
        => _inner.GetBytes(ordinal, dataOffset, buffer, bufferOffset, length);
    public override char GetChar(int ordinal) => _inner.GetChar(ordinal);
    public override long GetChars(int ordinal, long dataOffset, char[]? buffer, int bufferOffset, int length)
        => _inner.GetChars(ordinal, dataOffset, buffer, bufferOffset, length);
    public override DateTime GetDateTime(int ordinal) => _inner.GetDateTime(ordinal);
    public override decimal GetDecimal(int ordinal) => _inner.GetDecimal(ordinal);
    public override double GetDouble(int ordinal) => _inner.GetDouble(ordinal);
    public override float GetFloat(int ordinal) => _inner.GetFloat(ordinal);
    public override Guid GetGuid(int ordinal) => _inner.GetGuid(ordinal);
    public override short GetInt16(int ordinal) => _inner.GetInt16(ordinal);
    public override int GetInt32(int ordinal) => _inner.GetInt32(ordinal);
    public override long GetInt64(int ordinal) => _inner.GetInt64(ordinal);
    public override string GetString(int ordinal) => _inner.GetString(ordinal);
    public override int GetValues(object[] values) => _inner.GetValues(values);
    public override IEnumerator GetEnumerator() => _inner.GetEnumerator();
    public override bool NextResult() => false;   // 单结果集：导出不跨表
    public override System.Data.DataTable GetSchemaTable() => _inner.GetSchemaTable()!;
    public override void Close() { /* 内层由调用方关闭 */ }
    protected override void Dispose(bool disposing) { /* 内层由调用方释放 */ }
}

public static class Exporter
{
    /// <summary>Excel 单工作表数据行上限（不含表头）。</summary>
    public const int XlsxMaxRows = 1_048_575;

    public const int HeadLimit = 5;

    /// <summary>关键词转安全文件名：非法字符替换为 '-'，超长截断，全空回退"未命名"。</summary>
    public static string CleanName(string name, int limit = 100)
    {
        const string illegal = "<>:\"/\\|?*";
        var sb = new StringBuilder(name.Length);
        foreach (var ch in name)
            sb.Append(illegal.Contains(ch) ? '-' : ch);
        var cleaned = sb.ToString().Trim();
        if (cleaned.Length == 0)
            cleaned = "未命名";
        return cleaned.Length > limit ? cleaned[..limit] : cleaned;
    }

    /// <summary>前几行结果的文本预览（用于界面日志显示）；无行返回 null。</summary>
    public static string? FormatPreview(IReadOnlyList<string> columns, IReadOnlyList<object?[]> head)
    {
        if (head.Count == 0)
            return null;
        var lines = new List<string>(head.Count + 1) { string.Join(" | ", columns) };
        foreach (var row in head)
            lines.Add(string.Join(" | ", row.Select(v => v is null ? "" : Convert.ToString(v, CultureInfo.InvariantCulture))));
        return string.Join("\n", lines);
    }

    /// <summary>
    /// 将游标流式写入 &lt;outRoot&gt;/&lt;directory&gt;/&lt;clean_name&gt;.&lt;ext&gt;。
    /// 返回 (输出路径, 行数, 是否截断, 预览行)。取消时删除半成品文件并抛 ExportCancelled。
    /// maxRowsOverride：测试注入的 xlsx 行数上限（0 = 用真实上限 1,048,575）。
    /// </summary>
    public static ExportResult ExportRows(
        string fmt, string directory, string filename, IReadOnlyList<string> columns,
        DbDataReader inner,
        string? outRoot = null, CancellationToken cancel = default,
        int checkEvery = 5000, int headLimit = HeadLimit, int maxRowsOverride = 0)
    {
        var root = outRoot ?? AppPaths.OutputDir;
        var outDir = Path.Combine(root, directory);
        Directory.CreateDirectory(outDir);
        var ext = fmt == "csv" ? "csv" : "xlsx";
        var path = Path.Combine(outDir, $"{CleanName(filename)}.{ext}");

        // 截断仅对 xlsx 生效（Python 版 csv 分支无上限检查）
        var maxRows = ext == "csv" ? int.MaxValue
            : maxRowsOverride > 0 ? maxRowsOverride : XlsxMaxRows;
        using var reader = new CancellableReader(inner, headLimit, cancel, checkEvery, maxRows);
        try
        {
            if (ext == "csv")
                WriteCsv(path, columns, reader);
            else
                WriteXlsx(path, reader);
        }
        catch (ExportCancelled)
        {
            TryDelete(path);
            throw;
        }
        return new ExportResult(path, reader.RowsRead, reader.Truncated, reader.Head);
    }

    private static void WriteCsv(string path, IReadOnlyList<string> columns, CancellableReader reader)
    {
        // Python csv.writer 默认行为：\r\n 行尾、QUOTE_MINIMAL、utf-8-sig（Windows Excel 不乱码）
        using var fs = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.Read);
        using var writer = new StreamWriter(fs, new UTF8Encoding(encoderShouldEmitUTF8Identifier: true));
        writer.Write(string.Join(",", columns.Select(EscapeCsvField)));
        writer.Write("\r\n");
        while (reader.Read())
        {
            var fields = new string[reader.FieldCount];
            for (int c = 0; c < reader.FieldCount; c++)
                fields[c] = reader.IsDBNull(c) ? "" : Convert.ToString(reader.GetValue(c), CultureInfo.InvariantCulture) ?? "";
            writer.Write(string.Join(",", fields.Select(EscapeCsvField)));
            writer.Write("\r\n");
        }
    }

    private static string EscapeCsvField(string? field)
    {
        field ??= "";
        bool needQuote = field.Contains(',') || field.Contains('"')
                         || field.Contains('\n') || field.Contains('\r');
        return needQuote ? "\"" + field.Replace("\"", "\"\"") + "\"" : field;
    }

    private static void WriteXlsx(string path, CancellableReader reader)
    {
        // DataReader 通道：表头来自 GetName，行随 Read() 流式落盘（constant_memory 对应物）
        MiniExcel.SaveAs(path, reader, excelType: ExcelType.XLSX);
    }

    private static void TryDelete(string path)
    {
        try { File.Delete(path); } catch { /* 半成品清理失败不影响取消语义 */ }
    }
}
