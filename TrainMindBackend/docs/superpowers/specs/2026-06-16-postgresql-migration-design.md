# RuoYi-Vue 改造支持 PostgreSQL — 设计文档

- 日期：2026-06-16
- 分支：springboot3
- 参考：https://gitee.com/zbbtest/Ruoyi-PostgreSQL

## 1. 目标与策略

将本项目（RuoYi-Vue，Spring Boot 3 多模块）**完全切换**为 PostgreSQL，移除 MySQL 支持（不做双方言并存）。

范围边界：
- ✅ 依赖与数据源配置切换
- ✅ Mapper XML 的 SQL 方言改写（system + quartz）
- ✅ 提供 PostgreSQL 版本的建表 + 初始化数据脚本
- ❌ **暂不改造代码生成器（ruoyi-generator）** —— 见“已知遗留项”
- ❌ 不删除原 MySQL SQL 脚本（保留便于对照）

PostgreSQL 目标版本：12+（参考项目使用 12.3）。

## 2. 依赖与数据源配置

### 2.1 `ruoyi-admin/pom.xml`

移除 MySQL 驱动：

```xml
<!-- Mysql驱动包 -->
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
</dependency>
```

替换为 PostgreSQL 驱动（版本由 Spring Boot 3 BOM 统一管理，无需手动指定）：

```xml
<!-- PostgreSQL驱动包 -->
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>
```

### 2.2 `ruoyi-admin/src/main/resources/application-druid.yml`

| 配置项 | 原值（MySQL） | 新值（PostgreSQL） |
|---|---|---|
| `driverClassName` | `com.mysql.cj.jdbc.Driver` | `org.postgresql.Driver` |
| master `url` | `jdbc:mysql://localhost:3306/ry-vue?useUnicode=...` | `jdbc:postgresql://localhost:5432/ry-vue` |
| `validationQuery` | `SELECT 1 FROM DUAL` | `SELECT 1` |
| Druid `wall.config` | （默认 mysql） | 增加 `db-type: postgresql`，避免防火墙误拦 PG 语法 |

> 默认端口 5432；用户名/密码沿用本地占位（root/password 改为 postgres 占位）。

## 3. Mapper XML 方言改写

涉及 14 个源文件，共约 44 处改写（不含 `target/` 编译产物）。

### 3.1 `sysdate()` → `now()`（28 处）

| 文件 | 处数 |
|---|---|
| `ruoyi-system/.../SysUserMapper.xml` | 5 |
| `ruoyi-system/.../SysConfigMapper.xml` | 2 |
| `ruoyi-system/.../SysDeptMapper.xml` | 2 |
| `ruoyi-system/.../SysDictDataMapper.xml` | 2 |
| `ruoyi-system/.../SysDictTypeMapper.xml` | 2 |
| `ruoyi-system/.../SysMenuMapper.xml` | 2 |
| `ruoyi-system/.../SysNoticeMapper.xml` | 2 |
| `ruoyi-system/.../SysNoticeReadMapper.xml` | 2 |
| `ruoyi-system/.../SysPostMapper.xml` | 2 |
| `ruoyi-system/.../SysRoleMapper.xml` | 2 |
| `ruoyi-system/.../SysLogininforMapper.xml` | 1 |
| `ruoyi-system/.../SysOperLogMapper.xml` | 1 |
| `ruoyi-quartz/.../SysJobMapper.xml` | 2 |
| `ruoyi-quartz/.../SysJobLogMapper.xml` | 1 |

### 3.2 `ifnull(x,'')` → `coalesce(x,'')`（4 处）

- `SysMenuMapper.xml` 第 32 / 53 / 59 / 78 行

### 3.3 保留字反引号 `` `query` `` → 双引号 `"query"`（6 处）

- `SysMenuMapper.xml` 第 32 / 53 / 59 / 78 / 149 / 173 行

### 3.4 `find_in_set(#{deptId}, ancestors)` → PG 数组写法（3 处）

改写为：`#{deptId} = ANY(string_to_array(ancestors, ','))`

- `SysDeptMapper.xml` 第 78 / 82 行
- `SysUserMapper.xml` 第 83 行（子查询内）

说明：`ancestors` 为逗号分隔字符串（如 `0,100,101`）。`string_to_array` 拆为数组后用 `ANY` 判断成员，语义等价且清晰。

### 3.5 `date_format(col,'%Y%m%d')` → `to_char(col::date,'yyyyMMdd')`（10 处）

模式：
```
-- MySQL
and date_format(create_time,'%Y%m%d') >= date_format(#{params.beginTime},'%Y%m%d')
-- PostgreSQL
and to_char(create_time,'yyyyMMdd') >= to_char(#{params.beginTime}::date,'yyyyMMdd')
```

- `SysConfigMapper.xml` 第 54 / 57 行
- `SysDictTypeMapper.xml` 第 36 / 39 行
- `SysRoleMapper.xml` 第 49 / 52 行
- `SysUserMapper.xml` 第 77 / 80 行
- `SysJobLogMapper.xml` 第 41 / 44 行

说明：前端传入 `params.beginTime/endTime` 为 `yyyy-MM-dd` 字符串，PG 需 `::date` 显式转型后才能 `to_char`。列本身（`create_time`）已是 `timestamp`，可直接 `to_char`。PG 格式串 `yyyyMMdd`：`yyyy` 四位年、`MM` 两位月、`dd` 两位日。

## 4. SQL 脚本

新增两个脚本到 `sql/` 目录，原 MySQL 脚本保留：
- `sql/ry_postgresql.sql` —— 业务表 + 初始化数据（源自 `ry_20260417.sql`）
- `sql/quartz_postgresql.sql` —— Quartz 调度表（源自 `quartz.sql`）

### 4.1 类型与语法映射

| MySQL | PostgreSQL |
|---|---|
| `int/bigint ... AUTO_INCREMENT` 主键 | `SERIAL` / `BIGSERIAL` |
| `bigint(20)` | `int8` |
| `int(11)` | `int4` |
| `tinyint` | `int2` |
| `datetime` | `timestamp` |
| `varchar(N)` | `varchar(N)`（不变） |
| `` `col` ``（反引号） | `"col"`（双引号，仅保留字需要） |
| `ENGINE=InnoDB AUTO_INCREMENT=x DEFAULT CHARSET=utf8mb4` | 删除 |
| 列内联 `COMMENT '...'` | 独立 `COMMENT ON COLUMN tbl.col IS '...'` |
| 表 `COMMENT='...'` | 独立 `COMMENT ON TABLE tbl IS '...'` |
| `KEY` / `UNIQUE KEY` | 独立 `CREATE INDEX` / `CREATE UNIQUE INDEX` |

### 4.2 自增序列修正（关键）

初始化数据脚本显式插入了主键 id（如 `sys_user.user_id=1`、`sys_dept`、`sys_menu` 等）。使用 `BIGSERIAL` 时序列起始为 1，显式插入后不会推进序列，后续自增会与已存在 id 主键冲突。

因此脚本末尾对所有“显式插入 id 的自增表”追加序列重置：
```sql
SELECT setval('sys_user_user_id_seq', (SELECT max(user_id) FROM sys_user));
-- ... 其余各表同理
```

## 5. 测试与验证

无现成自动化测试，采用手动冒烟验证：

1. **编译**：`mvn clean compile` 通过（确认依赖替换无误）。
2. **建库**：PostgreSQL 中执行两个 PG 脚本，确认建表 + 初始数据成功、序列 `setval` 正确。
3. **启动**：应用连上 PG 正常启动（Druid 连接池、`validationQuery` 生效）。
4. **核心功能冒烟**：
   - 登录 —— 验证 `SysUserMapper` 查询与 `now()` 更新登录时间。
   - 用户列表带日期范围筛选 —— 验证 `to_char` 改写。
   - 部门树 / 用户按部门查询 —— 验证 `find_in_set` → `ANY` 改写。
   - 菜单加载 —— 验证 `"query"` 双引号 + `coalesce`。
   - 新增数据两次 —— 验证 `BIGSERIAL` 序列不与初始 id 冲突。

## 6. 已知遗留项（本期不做）

- **代码生成器（ruoyi-generator）**：本期完全未改，PG 下整体不可用。具体问题：
  - `GenTableMapper.xml` / `GenTableColumnMapper.xml` 仍使用 MySQL `information_schema` + `select database()` 查询，且 PG 的 `information_schema.tables` 无 `create_time/update_time` 列 —— 导入表结构功能不可用。
  - 上述两个 mapper 的 gen_table 增/改/列表语句仍含 `sysdate()`、`date_format(...,'%Y%m%d')`（GenTableColumnMapper 第 88/109 行，GenTableMapper 第 72/75/92/95/173/202 行）—— 连保存/查询生成器配置本身也会失败。
  - 列类型→Java 映射、`sql.vm` DDL 模板也未适配 PG。
  - 后续需要使用生成器时再单独立项处理（其中 sysdate/date_format 部分与本期 system/quartz 的改法完全一致）。
- **原 MySQL 脚本与注释**：保留不动，便于对照与回退。
