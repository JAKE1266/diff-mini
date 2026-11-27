# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式,
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.1] - 2026-11-27

### 修复
- unified 与 word 模式的 hunk 范围遵循统一 diff 格式：空范围保留 `,0`，单行省略 `,1`
- CLI 标准输入、输出与错误流固定 UTF-8，修复 Windows 默认编码下的中文乱码与管道解码失败

### 变更
- 新增空文件、单行、零上下文与旧编码管道的回归测试，单元测试增至 29 项
- CI 构建 wheel/sdist，并在三系统 × Python 3.8/3.9/3.11/3.13 下安装真实 wheel 后运行冒烟与测试

## [0.1.0] - 2026-11-21

### 新增
- 核心功能实现(纯标准库,零第三方依赖)
- CLI 命令行入口
- 25 个单元测试
- GitHub Actions 三系统 × 多版本 CI
- 中文 README 与 MIT 许可证

### 变更
- 补齐徽章、项目结构与本日志,与其他仓库文档标准统一
