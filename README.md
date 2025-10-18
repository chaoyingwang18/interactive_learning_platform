# Interactive Learning Platform 环境搭建与运行指南

## 1. 打开 Codespace
在 GitHub 上选择“Open in Codespaces”或在本地 VS Code 远程连接 Codespace。

## 2. 创建并激活 Python 虚拟环境
建议在项目根目录（即包含 `interactive_learning_platform` 文件夹的目录）执行：

```bash
python3 -m venv .venv
cd /workspaces/interactive_learning_platform
source .venv/bin/activate
```

## 3. 安装依赖包
进入 `interactive_learning_platform` 目录，安装依赖：

```bash
cd interactive_learning_platform
pip install -r requirements.txt
```

如遇依赖缺失，可手动安装，例如：
```bash
pip install flask flask_login
```

## 4. 初始化数据库（如有需要）
如需初始化数据库，可运行：
```bash
python init_db.py
```

## 5. 运行 Web 应用
确保虚拟环境已激活，当前目录为 `interactive_learning_platform`，运行：
```bash
cd interactive_learning_platform
python src/main.py
```

或使用 Flask 默认端口：
```bash
flask run
```

## 6. 访问应用
默认运行在 `http://localhost:5000`，可在浏览器中访问。

---

### 常见问题
- **ModuleNotFoundError**：请确认已激活虚拟环境，并在虚拟环境中安装依赖。
- **requirements.txt 未找到**：请确认当前目录为 `interactive_learning_platform`。
- **端口冲突或无法访问**：检查 Codespace 端口转发设置。

如有其他问题，请查阅 `System_Documentation.md` 或联系项目维护者。
