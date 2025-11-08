# 各标签页统一导入，便于主程序动态加载
from .call_num_piece_tab import create as create_call_num_piece_tab, CallNumPieceTab
from .call_num_tab import create as create_call_num_tab, CallNumTab
from .isbn_tab import create as create_isbn_tab, IsbnTab
from .title_tab import create as create_title_tab, TitleTab

# 可选：标签页注册表，便于遍历和动态加载
TAB_MODULES = [
	{
		'name': CallNumPieceTab.TAB_NAME,
		'title': CallNumPieceTab.TAB_TITLE,
		'create': create_call_num_piece_tab,
		'class': CallNumPieceTab,
	},
	{
		'name': CallNumTab.TAB_NAME,
		'title': CallNumTab.TAB_TITLE,
		'create': create_call_num_tab,
		'class': CallNumTab,
	},
	{
		'name': IsbnTab.TAB_NAME,
		'title': IsbnTab.TAB_TITLE,
		'create': create_isbn_tab,
		'class': IsbnTab,
	},
	{
		'name': TitleTab.TAB_NAME,
		'title': TitleTab.TAB_TITLE,
		'create': create_title_tab,
		'class': TitleTab,
	},
]
