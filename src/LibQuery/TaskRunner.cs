// 后台任务框架（对应 Python 版 gui/worker.py 的 TaskRunner/Reporter）。
// 反卡死铁律与 Python 版一致：
// 1. 所有耗时操作（导入、检索、批量导出）一律在后台线程执行，UI 线程只做交互；
// 2. 进度/消息经 Progress<T> 自动封送回 UI 线程，完成/失败经控件 BeginInvoke 封送；
// 3. 任务运行期间统一禁用控件（BusyChanged），取消经 CancellationToken 协作式生效。

namespace LibQuery;

/// <summary>传给 job 的回调集合：进度与文本消息均安全回主线程。</summary>
internal sealed class Reporter
{
    private readonly IProgress<(int Done, int Total)>? _progress;
    private readonly IProgress<string>? _message;

    public Reporter(IProgress<(int Done, int Total)>? progress, IProgress<string>? message)
    {
        _progress = progress;
        _message = message;
    }

    public void Progress(int done, int total) => _progress?.Report((done, total));

    public void Message(string text) => _message?.Report(text);
}

internal sealed class TaskRunner
{
    private readonly Control _invoker;
    private CancellationTokenSource? _cts;

    public bool Busy { get; private set; }

    public event Action<bool>? BusyChanged;

    public TaskRunner(Control invoker) => _invoker = invoker;

    public void Cancel() => _cts?.Cancel();

    public void Start(
        Func<Reporter, CancellationToken, object?> job,
        Action<object?> onFinished,
        Action<string> onFailed,
        Action<string>? onMessage = null,
        Action<int, int>? onProgress = null)
    {
        if (Busy)
            return;  // 同一 runner 同时只跑一个任务
        var cts = new CancellationTokenSource();
        _cts = cts;
        var progress = onProgress is null
            ? null
            : new Progress<(int Done, int Total)>(t => onProgress!(t.Done, t.Total));
        var messages = onMessage is null ? null : new Progress<string>(m => onMessage!(m));
        var reporter = new Reporter(progress, messages);

        Busy = true;
        BusyChanged?.Invoke(true);
        Task.Run(() =>
        {
            try
            {
                var result = job(reporter, cts.Token);
                Post(() => onFinished(result));
            }
            catch (Exception err)  // 后台线程兜底，避免异常静默
            {
                Post(() => onFailed($"{err.GetType().Name}: {err.Message}"));
            }
            finally
            {
                Post(() =>
                {
                    Busy = false;
                    _cts = null;
                    cts.Dispose();
                    BusyChanged?.Invoke(false);
                });
            }
        });
    }

    private void Post(Action action)
    {
        if (_invoker.IsDisposed || !_invoker.IsHandleCreated)
            return;
        if (_invoker.InvokeRequired)
            _invoker.BeginInvoke(action);
        else
            action();
    }
}
