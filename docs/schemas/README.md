# V2 Schema 说明

这些 schema 定义了 `PSD Smart Cut V2` 的目标机器可读协议。

在正式 schema 之外，V2 还强制要求一层分析协议，用来承接截图理解到资源规划之间的空档。

主入口应是页面层，也就是：

- `PageModel`

页面层引用：

- 区域
- 组件实例

组件层定义：

- 可复用的 UI 语义
- 状态
- 文本槽位
- 资源引用

资源层定义：

- 唯一物理资源
- 稳定文件身份
- 复用信息

## 文件

- [page.schema.json](./page.schema.json)
- [region.schema.json](./region.schema.json)
- [component.schema.json](./component.schema.json)
- [resource.schema.json](./resource.schema.json)

## 对应的协议层

```text
pages/
components/
resources/
analysis/
```

## 使用原则

- 这些 schema 描述的是 V2 目标协议，不是旧 heuristic pipeline 的输出
- `analysis/` 用于审阅和对齐，故意不放进正式机器协议里
- `pages/` 应作为主机器入口
- `components/` 和 `resources/` 必须保持身份分离

## 分析层建议文件

虽然 `analysis/` 不放入正式 schema，但建议固定产出：

- `page-analysis.md / json`
- `frontend-analysis.md / json`
- `implementation-decision.json`

这层文件负责回答：

- 页面和模块是什么
- 组件如何拆成前端子部件
- 每个子部件应走 `image / css / text / svg` 中哪一类实现

详细协议见：

- [前端分析协议](../FRONTEND-ANALYSIS-SPEC.md)
