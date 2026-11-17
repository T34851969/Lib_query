// 生成合成馆藏数据库，用于性能压测（默认 100 万行）。
// 用法：dotnet run -c Release --project bench/LibBench -- [--rows 1000000] [--output 路径]
// 生成的库结构与正式库一致（books + 索引 + FTS5 trigram），
// 可用于对比 FTS 前后的题名检索耗时（对应 Python 版 scripts/build_synth_db.py）。

using System.Diagnostics;
using LibQuery.Core;

int rows = 1_000_000;
string? output = null;
for (int i = 0; i < args.Length - 1; i++)
{
    if (args[i] == "--rows")
        rows = int.Parse(args[i + 1]);
    if (args[i] == "--output")
        output = args[i + 1];
}

var outPath = output ?? Path.Combine(Environment.CurrentDirectory, "synthetic_馆藏.db");
if (File.Exists(outPath))
    File.Delete(outPath);

var t0 = Stopwatch.StartNew();
SynthDb.MakeBooksDb(outPath, rows, withFts: true);
t0.Stop();

Console.WriteLine($"数据 + 索引 + FTS 构建完成：{rows} 行，耗时 {t0.Elapsed.TotalSeconds:F1} 秒");
Console.WriteLine($"输出: {outPath}");
return 0;
