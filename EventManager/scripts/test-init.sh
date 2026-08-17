#!/bin/bash
# ═══════════════════════════════════════════════════════
# 测试初始化脚本
# 验证 init-all.sh 脚本的功能
# ═══════════════════════════════════════════════════════

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🧪 测试初始化脚本${NC}"
echo ""

# 测试1: 检查脚本是否存在
echo -e "${YELLOW}测试1: 检查脚本文件${NC}"
if [[ -f "scripts/init-all.sh" ]]; then
    echo -e "${GREEN}✅ scripts/init-all.sh 存在${NC}"
else
    echo -e "${RED}❌ scripts/init-all.sh 不存在${NC}"
    exit 1
fi

# 测试2: 检查脚本是否可执行
echo -e "${YELLOW}测试2: 检查执行权限${NC}"
if [[ -x "scripts/init-all.sh" ]]; then
    echo -e "${GREEN}✅ 脚本有执行权限${NC}"
else
    echo -e "${RED}❌ 脚本没有执行权限${NC}"
    exit 1
fi

# 测试3: 检查帮助信息
echo -e "${YELLOW}测试3: 检查帮助信息${NC}"
if ./scripts/init-all.sh --help | grep -q "EventFlow 一键初始化脚本"; then
    echo -e "${GREEN}✅ 帮助信息正常${NC}"
else
    echo -e "${RED}❌ 帮助信息异常${NC}"
    exit 1
fi

# 测试4: 检查 Makefile 命令
echo -e "${YELLOW}测试4: 检查 Makefile 命令${NC}"
if make help | grep -q "init-all"; then
    echo -e "${GREEN}✅ Makefile 命令已添加${NC}"
else
    echo -e "${RED}❌ Makefile 命令未找到${NC}"
    exit 1
fi

# 测试5: 检查文档
echo -e "${YELLOW}测试5: 检查文档文件${NC}"
if [[ -f "scripts/README.md" ]]; then
    echo -e "${GREEN}✅ scripts/README.md 存在${NC}"
else
    echo -e "${RED}❌ scripts/README.md 不存在${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 所有测试通过！${NC}"
echo ""
echo "初始化脚本已就绪，你可以使用以下命令："
echo ""
echo "  make init-all          # 一键初始化（推荐）"
echo "  make init-all-local    # 本地模式初始化"
echo "  make init-all-docker   # Docker 模式初始化"
echo "  make init-python       # 只初始化 Python 栈"
echo "  make init-go           # 只初始化 Go 栈"
echo ""
echo "详细说明请查看: scripts/README.md"
