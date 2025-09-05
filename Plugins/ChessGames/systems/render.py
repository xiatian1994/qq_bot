"""
渲染系统
"""

from Core.tools.browser import browser


class RenderSystem:
    """渲染系统 - 简单封装"""

    def __init__(self):
        """初始化渲染系统"""
        pass  # 不需要任何初始化

    async def render_to_image(self, template_name: str, data: dict, width: int = None) -> str:
        """
        渲染模板为图片

        Args:
            template_name: 模板文件名（如 'tictactoe_board.html'）
            data: 模板数据
            width: 图片宽度，None为自适应

        Returns:
            纯base64图片数据（不包含data:image/png;base64,前缀）
        """
        # 构建模板路径：ChessGames/templates/xxx.html
        template_path = f'ChessGames/templates/{template_name}'

        # 直接使用系统级浏览器管理器
        return browser.render(template_path, data, width)
