// 检索页：单次 + 批量检索的共用 UI 与任务编排（对应 Python 版 gui/search_tab.py）。
// 四个检索页仅由 SearchSpecs 配置差异化；busy 期间统一禁用输入并显示进度，可随时取消。

using LibQuery.Core;

namespace LibQuery;

internal sealed class SearchTab : UserControl
{
    private readonly LibraryService _service;
    private readonly SearchSpec _spec;
    private readonly Action<string> _log;
    private readonly TaskRunner _runner;
    private string _filePath = "";

    private TextBox _keywordEdit = null!;
    private Button _singleBtn = null!;
    private Button _fileBtn = null!;
    private Button _batchBtn = null!;
    private Button _cancelBtn = null!;
    private RadioButton _singleXlsx = null!;
    private RadioButton _batchXlsx = null!;
    private TextBox _batchEdit = null!;
    private ProgressBar _progress = null!;

    public SearchTab(LibraryService service, SearchSpec spec, Action<string> log)
    {
        _service = service;
        _spec = spec;
        _log = log;
        _runner = new TaskRunner(this);
        _runner.BusyChanged += OnBusyChanged;
        BuildUi();
    }

    // ---- UI ----

    private void BuildUi()
    {
        Dock = DockStyle.Fill;
        Padding = new Padding(10);

        var root = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1 };
        root.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        var rowStyles = new (SizeType Style, float Weight)[]
        {
            (SizeType.AutoSize, 0),   // 0 页头
            (SizeType.AutoSize, 0),   // 1 单次检索行
            (SizeType.AutoSize, 0),   // 2 输出格式
            (SizeType.Absolute, 1),   // 3 分隔线
            (SizeType.AutoSize, 0),   // 4 批量头
            (SizeType.Absolute, 116), // 5 批量输入（对应 Python 版 setFixedHeight(110)）
            (SizeType.AutoSize, 0),   // 6 批量格式
            (SizeType.Absolute, 24),  // 7 进度条
            (SizeType.AutoSize, 0),   // 8 提示
            (SizeType.Percent, 100),  // 9 底部填充
        };
        foreach (var (style, weight) in rowStyles)
            root.RowStyles.Add(new RowStyle(style, weight));

        // 页头
        var header = new Label
        {
            Text = _spec.Label,
            AutoSize = true,
            Margin = new Padding(0),
            Font = new Font(Font.FontFamily, 11.25F, FontStyle.Bold),  // 对应 Python 版 QSS 15px 粗体
            ForeColor = Color.FromArgb(0x09, 0x3E, 0x55),
        };
        root.Controls.Add(header, 0, 0);

        // 单次检索行
        var singleRow = NewRowPanel((SizeType.AutoSize, 0), (SizeType.Percent, 100), (SizeType.AutoSize, 0));
        var kwLabel = new Label { Text = "请输入关键词：", AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(0, 8, 4, 0) };
        _keywordEdit = new TextBox { Dock = DockStyle.Fill, PlaceholderText = _spec.Tip, Margin = new Padding(0, 5, 8, 0) };
        _keywordEdit.KeyDown += (_, e) =>
        {
            if (e.KeyCode == Keys.Enter)
            {
                e.SuppressKeyPress = true;
                OnSingle();
            }
        };
        _singleBtn = new Button { Text = "开始搜索", AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(0, 5, 0, 0) };
        _singleBtn.Click += (_, _) => OnSingle();
        singleRow.Controls.Add(kwLabel, 0, 0);
        singleRow.Controls.Add(_keywordEdit, 1, 0);
        singleRow.Controls.Add(_singleBtn, 2, 0);
        root.Controls.Add(singleRow, 0, 1);

        // 输出格式行（单次）
        var fmtRow = NewRowPanel((SizeType.AutoSize, 0), (SizeType.AutoSize, 0), (SizeType.AutoSize, 0));
        _singleXlsx = new RadioButton { Text = ".xlsx", AutoSize = true, Checked = true, Margin = new Padding(0, 6, 8, 0) };
        var singleCsv = new RadioButton { Text = ".csv", AutoSize = true, Margin = new Padding(0, 6, 0, 0) };
        fmtRow.Controls.Add(RightPad("输出格式：", 4), 0, 0);
        fmtRow.Controls.Add(_singleXlsx, 1, 0);
        fmtRow.Controls.Add(singleCsv, 2, 0);
        root.Controls.Add(fmtRow, 0, 2);

        // 分隔线
        root.Controls.Add(new Panel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(0xC8, 0xC8, 0xC8), Margin = new Padding(0, 6, 0, 0) }, 0, 3);

        // 批量头
        var batchHead = NewRowPanel((SizeType.Percent, 100), (SizeType.AutoSize, 0), (SizeType.AutoSize, 0));
        var batchLabel = new Label
        {
            Text = "批量检索（每行一个关键词，\n或从文件导入）：",
            AutoSize = true,
            Anchor = AnchorStyles.Left,
            Margin = new Padding(0, 8, 0, 0),
        };
        _fileBtn = new Button { Text = "选择文件…", AutoSize = true, Anchor = AnchorStyles.Right, Margin = new Padding(0, 5, 8, 0) };
        _fileBtn.Click += (_, _) => OnPickFile();
        _batchBtn = new Button { Text = "开始搜索（批量）", AutoSize = true, Anchor = AnchorStyles.Right, Margin = new Padding(0, 5, 0, 0) };
        _batchBtn.Click += (_, _) => OnBatch();
        batchHead.Controls.Add(batchLabel, 0, 0);
        batchHead.Controls.Add(_fileBtn, 1, 0);
        batchHead.Controls.Add(_batchBtn, 2, 0);
        root.Controls.Add(batchHead, 0, 4);

        // 批量输入
        _batchEdit = new TextBox
        {
            Dock = DockStyle.Fill,
            Multiline = true,
            ScrollBars = ScrollBars.Vertical,
            Margin = new Padding(0, 6, 0, 0),
            PlaceholderText = "每行一个关键词；留空时使用已选择的文件",
        };
        root.Controls.Add(_batchEdit, 0, 5);

        // 批量格式行 + 取消
        var batchFmt = NewRowPanel((SizeType.AutoSize, 0), (SizeType.AutoSize, 0), (SizeType.AutoSize, 0),
            (SizeType.Percent, 100), (SizeType.AutoSize, 0));
        _batchXlsx = new RadioButton { Text = ".xlsx", AutoSize = true, Checked = true, Margin = new Padding(0, 6, 8, 0) };
        var batchCsv = new RadioButton { Text = ".csv", AutoSize = true, Margin = new Padding(0, 6, 0, 0) };
        _cancelBtn = new Button { Text = "取消", AutoSize = true, Enabled = false, Anchor = AnchorStyles.Right, Margin = new Padding(0, 5, 0, 0) };
        _cancelBtn.Click += (_, _) => _runner.Cancel();
        batchFmt.Controls.Add(RightPad("批量输出格式：", 4), 0, 0);
        batchFmt.Controls.Add(_batchXlsx, 1, 0);
        batchFmt.Controls.Add(batchCsv, 2, 0);
        batchFmt.Controls.Add(_cancelBtn, 4, 0);
        root.Controls.Add(batchFmt, 0, 6);

        // 进度条
        _progress = new ProgressBar
        {
            Dock = DockStyle.Fill,
            Height = 18,
            Style = ProgressBarStyle.Marquee,
            Visible = false,
            Margin = new Padding(0, 6, 0, 0),
        };
        root.Controls.Add(_progress, 0, 7);

        // 提示
        var tip = new Label { Text = _spec.Tip, AutoSize = true, ForeColor = Color.Gray, Margin = new Padding(0, 6, 0, 0) };
        root.Controls.Add(tip, 0, 8);

        // 底部填充
        root.Controls.Add(new Panel { Dock = DockStyle.Fill, Margin = new Padding(0) }, 0, 9);

        Controls.Add(root);
    }

    private static TableLayoutPanel NewRowPanel(params (SizeType Style, float Weight)[] columns)
    {
        var panel = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink,
            ColumnCount = columns.Length,
            Margin = new Padding(0, 6, 0, 0),
        };
        foreach (var (style, weight) in columns)
            panel.ColumnStyles.Add(new ColumnStyle(style, weight));
        panel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        return panel;
    }

    private static Label RightPad(string text, int right) =>
        new() { Text = text, AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(0, 8, right, 0) };

    // ---- 任务执行 ----

    private string Fmt => _singleXlsx.Checked ? "xlsx" : "csv";
    private string BatchFmt => _batchXlsx.Checked ? "xlsx" : "csv";

    private void Start(Func<Reporter, CancellationToken, object?> job)
    {
        _progress.Style = ProgressBarStyle.Marquee;  // 先显示忙碌；批量收到进度后切换为确定区间
        _progress.Value = 0;
        _progress.Visible = true;
        _runner.Start(job,
            onProgress: OnProgress,
            onMessage: _log,
            onFinished: OnFinished,
            onFailed: OnFailed);
    }

    private void OnProgress(int done, int total)
    {
        if (total > 0 && _progress.Maximum != total)
        {
            _progress.Style = ProgressBarStyle.Blocks;
            _progress.Maximum = total;
        }
        _progress.Value = Math.Min(done, _progress.Maximum);
    }

    private void OnFinished(object? result)
    {
        _log(FormatResult(result));
        _progress.Visible = false;
    }

    private void OnFailed(string message)
    {
        _log($"任务失败: {message}");
        _progress.Visible = false;
    }

    private void OnBusyChanged(bool busy)
    {
        _singleBtn.Enabled = !busy;
        _batchBtn.Enabled = !busy;
        _fileBtn.Enabled = !busy;
        _keywordEdit.Enabled = !busy;
        _cancelBtn.Enabled = busy;
        if (!busy)
            _progress.Visible = false;
    }

    // ---- 动作 ----

    private void OnSingle()
    {
        var keyword = _keywordEdit.Text.Trim();
        if (keyword.Length == 0)
        {
            _log("请输入关键词。");
            return;
        }
        var fmt = Fmt;
        Start((_, ct) => _service.SearchSingle(_spec, keyword, fmt, ct));
    }

    private void OnBatch()
    {
        var lines = _batchEdit.Lines
            .Select(l => l.Trim())
            .Where(l => l.Length > 0)
            .ToArray();
        var fmt = BatchFmt;
        if (lines.Length > 0)
            Start((rep, ct) => _service.SearchBatch(_spec, lines, fmt, rep.Progress, ct));
        else if (_filePath.Length > 0)
            Start((rep, ct) => _service.SearchBatchFromFile(_spec, _filePath, fmt, rep.Progress, ct));
        else
            _log("请先输入关键词或选择文件。");
    }

    private void OnPickFile()
    {
        using var dialog = new OpenFileDialog
        {
            Title = "请选择TXT文件",
            Filter = "TXT文件 (*.txt)|*.txt|所有文件 (*)|*.*",
        };
        if (dialog.ShowDialog(this) == DialogResult.OK)
        {
            _filePath = dialog.FileName;
            _log($"已选择文件：{_filePath}");
        }
    }

    // ---- 结果展示 ----

    private static string FormatResult(object? result)
    {
        switch (result)
        {
            case BatchResult batch:
            {
                var lines = new List<string>(batch.Messages);
                foreach (var item in batch.Items)  // 批量结果：每关键词一行摘要
                {
                    if (item.Error is not null)
                        lines.Add($"✗ {item.Keyword}: {item.Error}");
                    else
                        lines.Add($"✓ {item.Keyword}: {item.Rows} 条 → {item.OutputFile ?? "（无输出）"}");
                }
                if (batch.Cancelled)
                    lines.Add("（任务已取消）");
                return string.Join("\n", lines);
            }
            case SearchResult single:
            {
                var lines = new List<string>(single.Messages);  // 单次结果
                if (single.Preview is not null)
                    lines.Add(single.Preview);
                if (single.OutputFile is not null)
                    lines.Add($"输出文件: {single.OutputFile}");
                return string.Join("\n", lines);
            }
            default:
                return result?.ToString() ?? "";
        }
    }
}
