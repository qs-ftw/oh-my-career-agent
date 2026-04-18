# Contributing to CareerAgent

Thank you for your interest in contributing to CareerAgent! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CareerAgent.git
   cd CareerAgent
   ```
3. Copy environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```
4. Start infrastructure:
   ```bash
   make dev
   ```

## Development Workflow

### Branch Naming

- `feature/description` — New features
- `fix/description` — Bug fixes
- `docs/description` — Documentation changes
- `refactor/description` — Code refactoring

### Commit Messages

Follow [Conventional Commits](https://www.conventioncommits.org/):

```
type(scope): description

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`

### Code Style

**Python (Backend)**
- Follow PEP 8
- Use `ruff` for linting and formatting
- Run: `make lint`

**TypeScript (Frontend)**
- Follow ESLint + Prettier config
- Run: `cd frontend && npm run lint`

### Testing

- All new features must include tests
- Run: `make test`
- Backend: `pytest` in `backend/tests/`
- Frontend: `vitest` in `frontend/src/`

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass: `make test`
4. Ensure linting passes: `make lint`
5. Update documentation if needed
6. Submit a PR using the PR template

### PR Checklist

- [ ] Tests pass locally
- [ ] Lint passes
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or clearly documented)
- [ ] PR description explains the "why" not just the "what"

## Project Structure

```
CareerAgent/
├── backend/          # Python FastAPI + LangGraph backend
├── frontend/         # React + Vite frontend
├── docs/             # Documentation
├── docker-compose.yml
├── Makefile
└── prd.md           # Product requirements (Chinese)
```

## Reporting Issues

- Use GitHub Issues
- Bug reports: use the Bug Report template
- Feature requests: use the Feature Request template

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 参与贡献

感谢你对 CareerAgent 的关注！本文档提供贡献指南。

### 开发环境搭建

1. Fork 本仓库
2. 克隆你的 Fork：
   ```bash
   git clone https://github.com/YOUR_USERNAME/CareerAgent.git
   cd CareerAgent
   ```
3. 复制环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 填入你的 API Key
   ```
4. 启动开发环境：
   ```bash
   make dev
   ```

### 分支命名

- `feature/描述` — 新功能
- `fix/描述` — Bug 修复
- `docs/描述` — 文档变更
- `refactor/描述` — 代码重构

### 提交信息

遵循 [Conventional Commits](https://www.conventioncommits.org/) 规范。

### PR 流程

1. 从 `main` 创建功能分支
2. 编写代码和测试
3. 确保所有测试通过：`make test`
4. 确保代码检查通过：`make lint`
5. 按需更新文档
6. 使用 PR 模板提交 Pull Request
