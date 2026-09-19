"""打包适配测试：PyInstaller 冻结环境下数据路径跟随可执行文件。"""
import importlib
import sys


def test_project_root_when_frozen(monkeypatch, tmp_path):
    import lib_query.db.core as core

    app_dir = tmp_path / "发行包" / "Lib_query"
    exe = app_dir / "Lib_query.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    try:
        importlib.reload(core)
        assert core.PROJECT_ROOT == app_dir
        assert core.DB_PATH == app_dir / "图书馆详细馆藏.db"
        assert core.OUTPUT_DIR == app_dir / "output"
    finally:
        monkeypatch.undo()
        importlib.reload(core)  # 恢复源码态路径

    assert core.PROJECT_ROOT == core.Path(__file__).resolve().parents[1]
