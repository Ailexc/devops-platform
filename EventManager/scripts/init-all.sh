#!/bin/bash
# ═══════════════════════════════════════════════════════
# EventFlow 一键初始化脚本
# 同时初始化 Python 和 Go 两个后端栈
# ═══════════════════════════════════════════════════════

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 默认参数
TOTAL_EVENTS=1000
CLEAR_EXISTING=false
MODE="auto"  # auto | docker | local
STACK="all"  # all | python | go

# 打印带颜色的信息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
header() { echo -e "\n${CYAN}══════════════════════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}══════════════════════════════════════════════════════${NC}\n"; }

# 显示帮助信息
show_help() {
    echo "EventFlow 一键初始化脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -t, --total NUM        生成事件数量 (默认: 1000)"
    echo "  -c, --clear            清空现有数据后重新初始化"
    echo "  -m, --mode MODE        运行模式: auto(自动检测) | docker | local"
    echo "  -s, --stack STACK      初始化的栈: all(全部) | python | go"
    echo "  -h, --help             显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                          # 自动检测模式，初始化两个栈各1000条数据"
    echo "  $0 -t 5000 -c               # 生成5000条数据，先清空现有数据"
    echo "  $0 -m docker -s python      # 只在Docker模式下初始化Python栈"
    echo "  $0 -m local -s go           # 只在本地模式下初始化Go栈"
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--total)
                TOTAL_EVENTS="$2"
                shift 2
                ;;
            -c|--clear)
                CLEAR_EXISTING=true
                shift
                ;;
            -m|--mode)
                MODE="$2"
                shift 2
                ;;
            -s|--stack)
                STACK="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检测运行环境
detect_environment() {
    if [[ "$MODE" == "auto" ]]; then
        if command -v docker &> /dev/null && docker info &> /dev/null; then
            if [[ -f "docker-compose.yml" ]] && docker compose ps &> /dev/null 2>&1; then
                MODE="docker"
                info "检测到 Docker 环境，使用 Docker 模式"
            else
                MODE="local"
                info "未检测到运行中的 Docker 服务，使用本地模式"
            fi
        else
            MODE="local"
            info "Docker 不可用，使用本地模式"
        fi
    fi
}

# 检查必要的依赖
check_dependencies() {
    local missing_deps=()
    
    if [[ "$STACK" == "all" || "$STACK" == "python" ]]; then
        if [[ "$MODE" == "local" ]]; then
            if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
                missing_deps+=("python3")
            fi
            if [[ ! -f ".venv/bin/python" ]]; then
                warning "未找到虚拟环境，将尝试使用系统 Python"
            fi
        fi
    fi
    
    if [[ "$STACK" == "all" || "$STACK" == "go" ]]; then
        if [[ "$MODE" == "local" ]]; then
            if ! command -v go &> /dev/null; then
                missing_deps+=("go")
            fi
        fi
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "缺少以下依赖: ${missing_deps[*]}"
        echo "请先安装这些依赖后再运行此脚本"
        exit 1
    fi
}

# 初始化 Python 栈
init_python() {
    header "🐍 初始化 Python 后端"
    
    local clear_flag=""
    if [[ "$CLEAR_EXISTING" == "true" ]]; then
        clear_flag="--clear"
    fi
    
    if [[ "$MODE" == "docker" ]]; then
        info "使用 Docker 模式初始化 Python 栈..."
        
        # RabbitMQ 由统一基础设施提供（devops-rabbitmq），此处仅确保其已运行
        info "确保统一 RabbitMQ (devops-rabbitmq) 运行..."
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^devops-rabbitmq$'; then
            info "统一 RabbitMQ 已就绪"
        else
            warning "未检测到 devops-rabbitmq，尝试通过统一基础设施启动..."
            ( cd "$(dirname "$0")/../../infra" && docker compose up -d rabbitmq )
        fi

        # 先拉起 api 容器，避免 exec 依赖"容器已在运行"（健壮性）
        # 注意：api 容器 command 自带 migrate（幂等），此处不可再 exec 重复 migrate，
        #   schema 刚清空时并发 migrate 会触发 pg_type_typname_nsp_index 唯一约束冲突。
        info "确保 api 容器运行（供 exec 执行 seed）..."
        docker compose up -d api
        
        # 等待容器内 migrate 完成（gunicorn 起来 = 迁移+collectstatic 完成）
        info "等待 api 容器就绪（容器内自动 migrate/collectstatic）..."
        local ready=0
        for i in $(seq 1 120); do
            if docker logs cmdb-event-api 2>/dev/null | grep -qE "Booting worker|Listening at|Application startup complete"; then
                ready=1; break
            fi
            sleep 1
        done
        if [[ "$ready" != "1" ]]; then
            error "api 容器未在 120s 内就绪"
            docker logs cmdb-event-api 2>/dev/null | tail -20
            return 1
        fi
        
        # 运行种子数据（seed_data 幂等）
        info "生成 $TOTAL_EVENTS 条模拟事件数据..."
        docker compose exec -T api python manage.py seed_data --total $TOTAL_EVENTS $clear_flag
        
    else
        info "使用本地模式初始化 Python 栈..."
        
        # 激活虚拟环境（如果存在）
        local python_cmd="python3"
        if [[ -f ".venv/bin/python" ]]; then
            python_cmd=".venv/bin/python"
            info "使用虚拟环境: $python_cmd"
        fi
        
        # 执行迁移
        info "执行数据库迁移..."
        cd backend
        $python_cmd manage.py migrate --noinput
        cd ..
        
        # 运行种子数据
        info "生成 $TOTAL_EVENTS 条模拟事件数据..."
        cd backend
        $python_cmd manage.py seed_data --total $TOTAL_EVENTS $clear_flag
        cd ..
    fi
    
    success "Python 栈初始化完成！"
}

# 初始化 Go 栈
init_go() {
    header "🐹 初始化 Go 后端"
    
    if [[ "$MODE" == "docker" ]]; then
        info "使用 Docker 模式初始化 Go 栈..."
        
        # 幂等种子随 go-api 启动时自动执行（空库首灌 / 非空跳过）
        # 需要强制重灌时设置 SEED_FORCE=true（与 make go-seed 等价）
        if [[ "$CLEAR_EXISTING" == "true" || "$CLEAR_EXISTING" == "1" ]]; then
            export SEED_FORCE=true
        fi
        export SEED_TOTAL=$TOTAL_EVENTS

        info "启动 go-api/go-worker（启动时自动执行迁移 + 幂等种子，共 $TOTAL_EVENTS 条）..."
        docker compose up -d go-api go-worker
        
    else
        info "使用本地模式初始化 Go 栈..."
        
        # 检查 Go 环境
        if ! command -v go &> /dev/null; then
            error "Go 未安装，请先安装 Go"
            exit 1
        fi
        
        # 检查 PostgreSQL 是否运行
        if ! pg_isready &> /dev/null 2>&1; then
            warning "PostgreSQL 未运行，请确保 PostgreSQL 服务已启动"
            warning "Go 栈需要 PostgreSQL 数据库"
            return 1
        fi
        
        # 运行 Go 种子数据
        info "生成 $TOTAL_EVENTS 条模拟事件数据..."
        cd backend-go
        
        # 设置环境变量（如果没有 .env 文件）
        if [[ ! -f ".env" ]]; then
            export DATABASE_URL="postgres://eventuser:eventpass@localhost:5433/eventdb_go"
            warning "使用默认数据库连接: $DATABASE_URL"
        fi
        
        go run ./cmd/seed
        cd ..
    fi
    
    success "Go 栈初始化完成！"
}

# 显示初始化摘要
show_summary() {
    header "📊 初始化摘要"
    
    echo -e "${GREEN}✅ 初始化完成！${NC}"
    echo ""
    echo "配置信息:"
    echo "  • 运行模式: $MODE"
    echo "  • 初始化栈: $STACK"
    echo "  • 事件数量: $TOTAL_EVENTS"
    echo "  • 清空现有数据: $CLEAR_EXISTING"
    echo ""
    
    if [[ "$STACK" == "all" || "$STACK" == "python" ]]; then
        echo "Python 后端:"
        if [[ "$MODE" == "docker" ]]; then
            echo "  • API 地址: http://api.event-management.orb.local"
            echo "  • 管理命令: docker compose exec api python manage.py <command>"
        else
            echo "  • 启动命令: make dev-backend"
            echo "  • 管理命令: cd backend && python manage.py <command>"
        fi
    fi
    
    if [[ "$STACK" == "all" || "$STACK" == "go" ]]; then
        echo ""
        echo "Go 后端:"
        if [[ "$MODE" == "docker" ]]; then
            echo "  • API 地址: http://api.go-event-management.orb.local"
            echo "  • 管理命令: docker compose exec go-api ./app <command>"
        else
            echo "  • 启动命令: make go-dev-api"
            echo "  • 种子数据: make go-seed"
        fi
    fi
    
    echo ""
    echo "常用命令:"
    echo "  • 查看服务状态: make ps"
    echo "  • 查看日志: make logs"
    echo "  • 重启服务: make restart"
    echo "  • 停止服务: make down"
}

# 主函数
main() {
    parse_args "$@"
    
    header "🚀 EventFlow 一键初始化"
    
    info "初始化参数:"
    echo "  • 事件数量: $TOTAL_EVENTS"
    echo "  • 清空现有数据: $CLEAR_EXISTING"
    echo "  • 运行模式: $MODE"
    echo "  • 初始化栈: $STACK"
    echo ""
    
    # 检测环境
    detect_environment
    
    # 检查依赖
    check_dependencies
    
    # 初始化指定的栈
    case $STACK in
        "all")
            init_python
            init_go
            ;;
        "python")
            init_python
            ;;
        "go")
            init_go
            ;;
        *)
            error "未知的栈类型: $STACK"
            echo "支持的栈类型: all, python, go"
            exit 1
            ;;
    esac
    
    # 显示摘要
    show_summary
}

# 运行主函数
main "$@"
