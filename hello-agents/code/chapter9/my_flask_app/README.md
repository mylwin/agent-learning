# my_flask_app

chapter9 的示例项目，用来配合 `CodebaseMaintainer` 做代码库探索与质量分析。

## 目录结构

```
my_flask_app/
├── app.py                  # Flask 应用工厂，定义路由
├── config.py               # 配置与环境变量
├── utils.py                # 金额格式化等工具函数
├── services/
│   ├── api_client.py       # 天气接口客户端
│   └── data_processor.py   # 销售数据读取与统计
└── data/
    └── sales_2024.csv      # 示例数据
```

## 运行

```bash
pip install -r requirements.txt
python app.py
```

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/sales/summary` | 销售额汇总（总额/订单数/均值） |
| GET | `/sales/top?limit=3` | 金额最高的商品 |
| GET | `/weather/<city>` | 查询城市天气 |

## 后续计划

- 补充单元测试与 lint 配置
- 销售统计支持按城市、月份筛选
- 增加接口缓存与错误降级
