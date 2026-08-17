#!/bin/bash
# ═══════════════════════════════════════════════════════
# EventFlow 初始化系统演示
# 展示各种初始化场景和用法
# ═══════════════════════════════════════════════════════

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  EventFlow 初始化系统演示${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
echo ""

# 演示1: 查看帮助
echo -e "${YELLOW}📚 演示1: 查看初始化脚本帮助${NC}"
echo "命令: ./scripts/init-all.sh --help"
echo ""
./scripts/init-all.sh --help
echo ""
echo -e "${GREEN}✅ 帮助信息显示正常${NC}"
echo ""

# 演示2: 查看 Makefile 命令
echo -e "${YELLOW}📚 演示2: 查看 Makefile 初始化命令${NC}"
echo "命令: make help | grep init"
echo ""
make help | grep init
echo ""
echo -e "${GREEN}✅ Makefile 命令显示正常${NC}"
echo ""

# 演示3: 模拟初始化（不实际执行）
echo -e "${YELLOW}📚 演示3: 模拟初始化命令${NC}"
echo "以下是你可以使用的初始化命令："
echo ""
echo -e "${BLUE}一键初始化（推荐）:${NC}"
echo "  make init-all              # 自动检测环境"
echo "  make init-all-local        # 本地模式"
echo "  make init-all-docker       # Docker 模式"
echo ""
echo -e "${BLUE}单独初始化:${NC}"
echo "  make init-python           # 只初始化 Python 栈"
echo "  make init-go               # 只初始化 Go 栈"
echo ""
echo -e "${BLUE}高级用法:${NC}"
echo "  ./scripts/init-all.sh -t 5000 -c      # 生成5000条数据，清空现有"
echo "  ./scripts/init-all.sh -s go -m docker  # 只初始化 Go 栈，Docker 模式"
echo ""

# 演示4: 项目结构
echo -e "${YELLOW}📚 演示4: 初始化相关文件结构${NC}"
echo "项目中的初始化相关文件："
echo ""
echo -e "${BLUE}核心脚本:${NC}"
echo "  scripts/init-all.sh        # 统一初始化脚本"
echo "  scripts/test-init.sh       # 脚本功能测试"
echo "  scripts/demo.sh            # 本演示脚本"
echo ""
echo -e "${BLUE}文档:${NC}"
echo "  scripts/README.md          # 使用指南"
echo "  scripts/EXAMPLES.md        # 使用示例"
echo "  scripts/ARCHITECTURE.md    # 技术架构"
echo "  scripts/SUMMARY.md         # 总结文档"
echo ""
echo -e "${BLUE}种子数据:${NC}"
echo "  backend/apps/event_store/management/commands/seed_data.py  # Python 种子数据"
echo "  backend-go/cmd/seed/main.go                               # Go 种子数据"
echo ""

# 演示5: 数据库信息
echo -e "${YELLOW}📚 演示5: 数据库配置信息${NC}"
echo "初始化使用的数据库配置："
echo ""
echo -e "${BLUE}Python 栈:${NC}"
echo "  数据库类型: SQLite"
echo "  数据库文件: backend/db.sqlite3"
echo "  迁移命令: cd backend && python manage.py migrate"
echo "  种子数据: cd backend && python manage.py seed_data"
echo ""
echo -e "${BLUE}Go 栈:${NC}"
echo "  数据库类型: PostgreSQL"
echo "  数据库名称: eventdb_go"
echo "  数据库端口: 5433"
echo "  迁移文件: backend-go/migrations/000001_init.up.sql"
echo "  种子数据: cd backend-go && go run ./cmd/seed"
echo ""

# 演示6: 快速开始
echo -e "${YELLOW}📚 演示6: 快速开始指南${NC}"
echo "3 步快速开始："
echo ""
echo -e "${GREEN}步骤1: 克隆项目${NC}"
echo "  git clone <repo-url>"
echo "  cd EventManager"
echo ""
echo -e "${GREEN}步骤2: 一键初始化${NC}"
echo "  make init-all"
echo ""
echo -e "${GREEN}步骤3: 启动开发${NC}"
echo "  make dev-backend   # Python 后端 (端口 8000)"
echo "  make dev-frontend  # 前端 (端口 3000)"
echo "  make go-dev-api    # Go 后端 (端口 8001)"
echo ""

# 演示7: 验证初始化
echo -e "${YELLOW}📚 演示7: 验证初始化结果${NC}"
echo "初始化完成后，你可以通过以下方式验证："
echo ""
echo -e "${BLUE}检查 Python 栈:${NC}"
echo "  curl http://localhost:8000/api/v1/events/ | jq '.count'"
echo ""
echo -e "${BLUE}检查 Go 栈:${NC}"
echo "  curl http://localhost:8001/api/v1/events/ | jq '.count'"
echo ""
echo -e "${BLUE}查看数据库:${NC}"
echo "  # Python (SQLite)"
echo "  sqlite3 backend/db.sqlite3 'SELECT COUNT(*) FROM api_event;'"
echo ""
echo "  # Go (PostgreSQL)"
echo "  psql -h localhost -p 5433 -U eventuser -d eventdb_go -c 'SELECT COUNT(*) FROM api_event;'"
echo ""

# 总结
echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  演示完成！${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}🎉 现在你可以开始使用初始化系统了！${NC}"
echo ""
echo "推荐命令："
echo -e "  ${BLUE}make init-all${NC}          # 一键初始化（推荐）"
echo -e "  ${BLUE}make init-all-local${NC}    # 本地模式初始化"
echo -e "  ${BLUE}make init-all-docker${NC}   # Docker 模式初始化"
echo ""
echo "详细文档请查看："
echo -e "  ${BLUE}scripts/README.md${NC}      # 使用指南"
echo -e "  ${BLUE}scripts/EXAMPLES.md${NC}    # 使用示例"
echo -e "  ${BLUE}scripts/ARCHITECTURE.md${NC} # 技术架构"
echo ""
echo -e "${YELLOW}提示: 运行 ./scripts/test-init.sh 可以测试脚本功能${NC}"
