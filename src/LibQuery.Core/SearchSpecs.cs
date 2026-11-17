// 四个检索页的声明式配置（顺序沿用旧版 TAB_MODULES）。

namespace LibQuery.Core;

public static class SearchSpecs
{
    public static readonly SearchSpec[] All =
    {
        new("call_num_piece", "索书号切片", "索书号切片检索", Searcher.ModePiece,
            Tip: "输入索书号切片（1~6 位），如 I247.5；5 位切片按前缀匹配"),
        new("call_num", "索书号", "索书号检索", Searcher.ModeExact, Column: "索书号",
            Tip: "输入完整索书号，精确匹配"),
        new("isbn", "ISBN", "ISBN 检索", Searcher.ModeExact, Column: "标准号",
            Tip: "输入完整标准号（ISBN），精确匹配"),
        new("title", "题名", "题名检索", Searcher.ModeTitle,
            Tip: "输入题名关键词；≥3 字符走 FTS 索引，更短的关键词回退全表扫描"),
    };
}
