# 贡献指南

感谢你对论文修改系统的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告问题

如果你发现了bug或有功能建议：

1. 检查 [Issues](../../issues) 确认问题是否已被报告
2. 创建新的 Issue，清晰描述问题或建议
3. 提供复现步骤（如果是bug）

### 提交代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码风格
- 为新功能添加单元测试
- 确保所有测试通过 (`pytest`)
- 更新相关文档

### 测试要求

提交前请确保：

```bash
# 运行所有测试
pytest

# 检查代码覆盖率（目标 >80%）
pytest --cov=src --cov-report=html

# 运行类型检查（如果使用）
mypy src/
```

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/your-username/paper-revision-system.git
cd paper-revision-system

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest
```

## 提交信息规范

使用清晰的提交信息：

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 代码重构
- `style:` 代码格式调整

示例：`feat: add citation validation feature`

## 行为准则

- 尊重所有贡献者
- 保持专业和友好的交流
- 接受建设性的批评
- 关注项目的最佳利益

## 问题？

如有疑问，请通过 Issues 联系我们。

感谢你的贡献！🎉
