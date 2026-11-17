// 数据目录定位（对应 Python 版 db/core.py 的 PROJECT_ROOT 约定）。
// 绿色单文件约定：数据库与 output/ 全部相对 exe 所在目录，
// 拷到 U 盘/新目录即整体迁移；不要放在 C:\Program Files 等受限路径下。

namespace LibQuery.Core;

public static class AppPaths
{
    public static string DataDir { get; } = AppContext.BaseDirectory;

    /// <summary>馆藏数据库（与旧 Python 版同名同位，旧库直接可用）。</summary>
    public static string DbPath => System.IO.Path.Combine(DataDir, "图书馆详细馆藏.db");

    public static string OutputDir => System.IO.Path.Combine(DataDir, "output");
}
