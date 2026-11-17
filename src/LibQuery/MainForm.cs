// 主窗口：四个检索页容器、只读日志面板与状态栏（对应 Python 版 gui/main_window.py）。
// 首次使用时引导导入馆藏 Excel；导入、检索等耗时操作全部经 TaskRunner 后台执行。

using System.Globalization;
using LibQuery.Core;

namespace LibQuery;

internal sealed class MainForm : Form
{
    private readonly LibraryService _service = new();
    private readonly TaskRunner _importRunner;

    private TabControl _tabs = null!;
    private TextBox _logBox = null!;
    private ProgressBar _importProgress = null!;
    private ToolStripStatusLabel _statusLabel = null!;

    public MainForm()
    {
        Text = "📚 图书馆 馆藏条目检索系统";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(900, 620);
        Size = new Size(1080, 720);

        _importRunner = new TaskRunner(this);
        BuildLayout();
        Shown += OnShown;
    }

    // ---- 布局 ----

    private void BuildLayout()
    {
        _tabs = new TabControl { Dock = DockStyle.Fill };
        foreach (var spec in SearchSpecs.All)
        {
            var page = new TabPage(spec.Label);
            page.Controls.Add(new SearchTab(_service, spec, Log) { Dock = DockStyle.Fill });
            _tabs.TabPages.Add(page);
        }

        var bottom = new Panel { Dock = DockStyle.Bottom, Height = 216 };
        _logBox = new TextBox
        {
            Dock = DockStyle.Fill,
            Multiline = true,
            ReadOnly = true,
            ScrollBars = ScrollBars.Vertical,
            Font = new Font("Consolas", 9F),
            BackColor = Color.White,
        };
        _importProgress = new ProgressBar
        {
            Dock = DockStyle.Top,
            Height = 10,
            Style = ProgressBarStyle.Marquee,
            Visible = false,
        };
        // 加入顺序决定停靠次序：先 Fill（日志），后 Top（进度条，先停靠）
        bottom.Controls.Add(_logBox);
        bottom.Controls.Add(_importProgress);

        _statusLabel = new ToolStripStatusLabel { Spring = true, TextAlign = ContentAlignment.MiddleLeft };
        var statusStrip = new StatusStrip { SizingGrip = false };
        statusStrip.Items.Add(_statusLabel);

        // 加入顺序决定停靠次序：先 Fill，后 Bottom/Bottom（后加入者先停靠 → 状态栏最底）
        Controls.Add(_tabs);
        Controls.Add(bottom);
        Controls.Add(statusStrip);
    }

    // ---- 日志 ----

    private void Log(string text) => _logBox.AppendText(text + Environment.NewLine);

    // ---- 数据库初始化与状态 ----

    private void OnShown(object? sender, EventArgs e)
    {
        if (_service.Exists())
        {
            RefreshCount();  // 状态栏文案会附带 FTS 缺失提示
            return;
        }

        var answer = MessageBox.Show(this, "未找到数据库，是否现在选择馆藏 Excel 文件导入？",
            "初始化", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (answer != DialogResult.Yes)
        {
            _statusLabel.Text = "未加载数据库：检索功能不可用";
            Log("已跳过导入；后续可通过重新启动程序完成初始化。");
            return;
        }
        PickAndImport();
    }

    private void PickAndImport()
    {
        using var dialog = new OpenFileDialog
        {
            Title = "请选择Excel文件",
            Filter = "Excel文件 (*.xlsx)|*.xlsx",
        };
        if (dialog.ShowDialog(this) != DialogResult.OK)
        {
            _statusLabel.Text = "未加载数据库：检索功能不可用";
            return;
        }
        var path = dialog.FileName;
        _importProgress.Visible = true;
        _importRunner.Start(
            (reporter, _) => _service.ImportExcel(path, reporter.Message),
            onFinished: result =>
            {
                _importProgress.Visible = false;
                var summary = (ImportSummary)result!;
                Log($"导入成功：{summary.Rows} 行，{summary.Columns.Count} 列，耗时 {summary.Seconds} 秒");
                RefreshCount();
            },
            onFailed: message =>
            {
                _importProgress.Visible = false;
                Log($"数据库初始化失败: {message}");
                _statusLabel.Text = "未加载数据库：检索功能不可用";
            },
            onMessage: Log);
    }

    private void RefreshCount()
    {
        _statusLabel.Text = "正在统计数据量…";
        Task.Run(() => _service.RecordCount())
            .ContinueWith(t =>
            {
                if (t.IsFaulted)
                    _statusLabel.Text = $"数据量统计失败: {t.Exception!.GetBaseException().Message}";
                else
                {
                    var suffix = _service.HasFts() ? "" : "（题名检索未建 FTS 索引）";
                    _statusLabel.Text =
                        $"数据库已加载，共 {t.Result.ToString("N0", CultureInfo.InvariantCulture)} 条{suffix}";
                }
            }, TaskScheduler.FromCurrentSynchronizationContext());
    }
}
