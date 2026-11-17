// 程序集加载时一次性初始化：注册 CodePages 编码提供程序。
// ExcelDataReader 默认依赖 Windows-1252 等代码页（.NET Core 起不再内置），
// 旧 .xls（BIFF）与部分 csv 场景必需；ModuleInitializer 保证任何入口都生效。

namespace LibQuery.Core;

internal static class RuntimeInit
{
    [System.Runtime.CompilerServices.ModuleInitializer]
    internal static void Init() =>
        System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
}
