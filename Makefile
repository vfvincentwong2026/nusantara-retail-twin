.PHONY: install seed validate test dev web calendar

PY ?= python

# 安装 Python 包（可编辑模式）
install:
	$(PY) -m pip install -e .

# 生成三档门店全量种子数据
seed:
	nrt seed --store-size all --region java

# 校验种子数据
validate:
	nrt validate data/seeds/store_500sqm.json data/seeds/store_2000sqm.json data/seeds/store_5000sqm.json

# 运行测试
test:
	$(PY) -m unittest discover -s tests -v

# 启动依赖服务（PostgreSQL + PostGIS，Phase 3 起需要）
db:
	docker compose up -d db

# 启动 API 服务（Phase 4 起提供）
dev:
	nrt serve --reload

# 前端（Phase 3 起提供）
web:
	@echo "web/ 尚未初始化（Phase 3）"

# 印尼节庆日历速查
calendar:
	nrt calendar --window
