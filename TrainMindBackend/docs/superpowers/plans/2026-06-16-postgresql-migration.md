# RuoYi-Vue 改造支持 PostgreSQL — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 RuoYi-Vue（Spring Boot 3）完全切换为 PostgreSQL，移除 MySQL 支持。

**Architecture:** 三层改动——(1) Maven 依赖与 Druid 数据源配置切换为 PG；(2) 14 个 Mapper XML 的 MySQL 专属 SQL 改写为 PG 方言；(3) 新增 PG 版建表与初始化数据脚本（含序列重置）。代码生成器与原 MySQL 脚本保留不动。

**Tech Stack:** Spring Boot 3、MyBatis、Druid、PostgreSQL 12+、Maven。

**设计文档：** `docs/superpowers/specs/2026-06-16-postgresql-migration-design.md`

**验证说明：** 本项目无单元测试框架覆盖 Mapper/SQL，验证以「编译通过 + 建库成功 + 启动冒烟」为准。每个任务给出明确的验证命令与预期。

**当前验证状态（2026-07-08）：**
- Task 1-8 已按当前源码与 PostgreSQL 临时库验证完成。
- Task 9 Step 1 全量编译已通过。
- Task 9 Step 2-3 启动应用与人工冒烟尚未执行。
- 验证命令使用项目本地 Linux 工具链：`source ../scripts/env.sh`，Maven 本地仓库为 `../.tools/m2/repository`。
- 为避免破坏现有 `ruoyi` 数据库，SQL 脚本在临时库 `trainmind_verify_codex` 执行验证，验证通过后已删除该临时库；最终建表数量为 31。
- Quartz 静态检查中，原计划的宽泛 `blob` 文本匹配会误报 `QRTZ_BLOB_TRIGGERS`、`blob_data` 与注释；本次验证按“无 MySQL `blob` 类型残留，二进制列使用 `bytea`”执行。

---

## 文件清单

| 文件 | 动作 | 责任 |
|---|---|---|
| `ruoyi-admin/pom.xml` | 修改 | 替换 MySQL 驱动为 PostgreSQL |
| `ruoyi-admin/src/main/resources/application-druid.yml` | 修改 | 数据源驱动/URL/校验语句/wall 方言 |
| `ruoyi-system/.../mapper/system/*.xml`（12 个） | 修改 | SQL 方言改写 |
| `ruoyi-quartz/.../mapper/quartz/SysJobMapper.xml`、`SysJobLogMapper.xml` | 修改 | SQL 方言改写 |
| `sql/ry_postgresql.sql` | 新建 | PG 业务表 + 初始数据 + 序列重置 |
| `sql/quartz_postgresql.sql` | 新建 | PG Quartz 表 |

---

## Task 1: 切换 Maven 依赖为 PostgreSQL

**Files:**
- Modify: `ruoyi-admin/pom.xml`（MySQL 驱动依赖块，约 33-37 行）

- [x] **Step 1: 替换驱动依赖**

将：
```xml
        <!-- Mysql驱动包 -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
        </dependency>
```
替换为：
```xml
        <!-- PostgreSQL驱动包 -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
```

- [x] **Step 2: 验证依赖解析**

Run: `mvn -q -pl ruoyi-admin -am dependency:tree -Dincludes=org.postgresql:postgresql`
Expected: 输出包含 `org.postgresql:postgresql:jar:<version>`，无报错。

- [x] **Step 3: Commit**

```bash
git add ruoyi-admin/pom.xml
git commit -m "build: 替换 MySQL 驱动为 PostgreSQL 驱动"
```

---

## Task 2: 切换 Druid 数据源配置为 PostgreSQL

**Files:**
- Modify: `ruoyi-admin/src/main/resources/application-druid.yml`

- [x] **Step 1: 改驱动类**

将 `driverClassName: com.mysql.cj.jdbc.Driver` 改为：
```yaml
        driverClassName: org.postgresql.Driver
```

- [x] **Step 2: 改 master url**

将 master 的 url 行改为：
```yaml
                url: jdbc:postgresql://localhost:5432/ry-vue
```

- [x] **Step 3: 改 validationQuery**

将 `validationQuery: SELECT 1 FROM DUAL` 改为：
```yaml
            validationQuery: SELECT 1
```

- [x] **Step 4: 给 wall 过滤器指定 PG 方言**

将：
```yaml
                wall:
                    config:
                        multi-statement-allow: true
```
改为：
```yaml
                wall:
                    db-type: postgresql
                    config:
                        multi-statement-allow: true
```

- [x] **Step 5: 验证 YAML 可解析 + 编译**

Run: `mvn -q clean compile`
Expected: BUILD SUCCESS（确认配置改动未破坏构建；YAML 语法错误会在打包阶段暴露，此处先确保编译通过）。

- [x] **Step 6: Commit**

```bash
git add ruoyi-admin/src/main/resources/application-druid.yml
git commit -m "config: Druid 数据源切换为 PostgreSQL"
```

---

## Task 3: 改写 `sysdate()` → `now()`（全部 mapper）

**Files:**
- Modify: `ruoyi-system/src/main/resources/mapper/system/` 下 12 个文件 + `ruoyi-quartz/src/main/resources/mapper/quartz/` 下 2 个文件（仅含 `sysdate()` 的）

涉及文件：SysUserMapper、SysConfigMapper、SysDeptMapper、SysDictDataMapper、SysDictTypeMapper、SysMenuMapper、SysNoticeMapper、SysNoticeReadMapper、SysPostMapper、SysRoleMapper、SysLogininforMapper、SysOperLogMapper、SysJobMapper、SysJobLogMapper。

- [x] **Step 1: 全量替换 `sysdate()` 为 `now()`**

仅作用于源码 mapper（不动 `target/`）。逐文件将所有 `sysdate()` 替换为 `now()`。可用脚本批量执行：

```bash
cd /d/ProjectCode/vibe/TrainMindAi/RuoYi-Vue
grep -rl 'sysdate()' --include=*.xml ruoyi-system/src ruoyi-quartz/src \
  | xargs sed -i 's/sysdate()/now()/g'
```

- [x] **Step 2: 验证无残留**

Run: `grep -rn 'sysdate()' --include=*.xml ruoyi-system/src ruoyi-quartz/src`
Expected: 无输出（退出码 1）。

- [x] **Step 3: 验证 now() 出现次数为 28**

Run: `grep -roE 'now\(\)' --include=*.xml ruoyi-system/src ruoyi-quartz/src | wc -l`
Expected: `28`（当前源码实测为 `29`，原因是代码版本较计划多 1 处 `now()`；无 `sysdate()` 残留）

- [x] **Step 4: Commit**

```bash
git add ruoyi-system/src ruoyi-quartz/src
git commit -m "fix(sql): sysdate() 改为 PostgreSQL now()"
```

---

## Task 4: 改写 SysMenuMapper（ifnull + 保留字 query）

**Files:**
- Modify: `ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml`

- [x] **Step 1: `ifnull` → `coalesce`**

将文件中所有 `ifnull(perms,'')` 改为 `coalesce(perms,'')`，所有 `ifnull(m.perms,'')` 改为 `coalesce(m.perms,'')`（共 4 处：第 32/53/59/78 行）。

```bash
cd /d/ProjectCode/vibe/TrainMindAi/RuoYi-Vue
sed -i 's/ifnull(/coalesce(/g' ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml
```

- [x] **Step 2: 反引号保留字 `` `query` `` → 双引号 `"query"`**

将该文件中 6 处 `` `query` ``（第 32/53/59/78/149/173 行）改为 `"query"`：

```bash
sed -i 's/`query`/"query"/g' ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml
```

- [x] **Step 3: 验证无 MySQL 残留**

Run: `grep -nE 'ifnull|\`' ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml`
Expected: 无输出（退出码 1）。

- [x] **Step 4: 验证替换结果**

Run: `grep -cE 'coalesce\(|"query"' ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml`
Expected: `10`（4 个 coalesce + 6 个 "query"）。当前源码实测为 `12`，原因是代码版本较计划多 2 处匹配；无 `ifnull` 和反引号残留。

- [x] **Step 5: Commit**

```bash
git add ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml
git commit -m "fix(sql): SysMenu ifnull→coalesce、保留字 query 改双引号"
```

---

## Task 5: 改写 find_in_set（SysDept + SysUser）

**Files:**
- Modify: `ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml`（第 78/82 行）
- Modify: `ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml`（第 83 行）

- [x] **Step 1: 改 SysDeptMapper 两处**

将：
```
find_in_set(#{deptId}, ancestors)
```
改为：
```
#{deptId} = ANY(string_to_array(ancestors, ','))
```

第 78 行上下文（改后）：
```xml
		select * from sys_dept where #{deptId} = ANY(string_to_array(ancestors, ','))
```
第 82 行上下文（改后）：
```xml
		select count(*) from sys_dept where status = 0 and del_flag = '0' and #{deptId} = ANY(string_to_array(ancestors, ','))
```

- [x] **Step 2: 改 SysUserMapper 第 83 行**

将子查询中的 `find_in_set(#{deptId}, ancestors)` 改为 `#{deptId} = ANY(string_to_array(ancestors, ','))`。改后该行：
```xml
			AND (u.dept_id = #{deptId} OR u.dept_id IN ( SELECT t.dept_id FROM sys_dept t WHERE #{deptId} = ANY(string_to_array(ancestors, ',')) ))
```

- [x] **Step 3: 验证无 find_in_set 残留**

Run: `grep -rn 'find_in_set' --include=*.xml ruoyi-system/src`
Expected: 无输出（退出码 1）。

- [x] **Step 4: Commit**

```bash
git add ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml
git commit -m "fix(sql): find_in_set 改为 PostgreSQL ANY(string_to_array)"
```

---

## Task 6: 改写 date_format → to_char（5 个 mapper）

**Files:**
- Modify: `SysConfigMapper.xml`(54/57)、`SysDictTypeMapper.xml`(36/39)、`SysRoleMapper.xml`(49/52)、`SysUserMapper.xml`(77/80)（均在 ruoyi-system）
- Modify: `ruoyi-quartz/.../SysJobLogMapper.xml`(41/44)

- [x] **Step 1: 批量改写 date_format**

模式：把列上的 `date_format(<col>,'%Y%m%d')` 改为 `to_char(<col>,'yyyyMMdd')`；把参数上的 `date_format(#{params.beginTime},'%Y%m%d')` 改为 `to_char(#{params.beginTime}::date,'yyyyMMdd')`，endTime 同理。

逐文件手动替换更安全。每个文件两行的目标形态如下（以 SysConfigMapper 为例）：

```xml
				and to_char(create_time,'yyyyMMdd') &gt;= to_char(#{params.beginTime}::date,'yyyyMMdd')
				and to_char(create_time,'yyyyMMdd') &lt;= to_char(#{params.endTime}::date,'yyyyMMdd')
```

其余文件列名不同（`r.create_time`、`u.create_time`、`create_time`），但结构一致：
- SysDictTypeMapper：列 `create_time`
- SysRoleMapper：列 `r.create_time`
- SysUserMapper：列 `u.create_time`（注意保留原大写 `AND`）
- SysJobLogMapper：列 `create_time`

- [x] **Step 2: 验证无 date_format 残留**

Run: `grep -rn 'date_format' --include=*.xml ruoyi-system/src ruoyi-quartz/src`
Expected: 无输出（退出码 1）。

- [x] **Step 3: 验证 to_char 出现次数为 20**

Run: `grep -roE 'to_char\(' --include=*.xml ruoyi-system/src ruoyi-quartz/src | wc -l`
Expected: `20`（10 行，每行 2 个 to_char）。

- [x] **Step 4: 编译确认 XML 合法**

Run: `mvn -q clean compile`
Expected: BUILD SUCCESS。

- [x] **Step 5: Commit**

```bash
git add ruoyi-system/src ruoyi-quartz/src
git commit -m "fix(sql): date_format 改为 PostgreSQL to_char"
```

---

## Task 7: 生成 PG 建表与初始化脚本 `sql/ry_postgresql.sql`

**Files:**
- Create: `sql/ry_postgresql.sql`
- Reference: `sql/ry_20260417.sql`（MySQL 源，722 行，含 sys_dept/sys_user/sys_post/sys_role/sys_menu/sys_user_role/sys_role_menu/sys_role_dept/sys_user_post/sys_oper_log/sys_dict_type/sys_dict_data/sys_config/sys_logininfor/sys_notice/sys_notice_read/gen_table/gen_table_column 等表）

- [x] **Step 1: 按映射规则转换全部建表语句**

按设计文档 §4.1 转换每张表。关键规则：
- 主键自增列 `bigint(20) not null auto_increment` → `bigserial`（其余 `int(N) auto_increment` → `serial`）。
- `bigint(N)`→`int8`、`int(N)`→`int4`、`tinyint(N)`→`int2`、`datetime`→`timestamp`、`char(N)`/`varchar(N)` 保持。
- 删除 `engine=innodb auto_increment=x comment='...'` 表尾，表注释改独立 `COMMENT ON TABLE`。
- 列内联 `comment '...'` 全部移除，改为脚本中独立 `COMMENT ON COLUMN <表>.<列> IS '...'`。
- `sysdate()` 在初始化 insert 中 → `now()`。

sys_dept 转换示例（建表部分）：
```sql
drop table if exists sys_dept;
create table sys_dept (
  dept_id           bigserial       not null,
  parent_id         int8            default 0,
  ancestors         varchar(50)     default '',
  dept_name         varchar(30)     default '',
  order_num         int4            default 0,
  leader            varchar(20)     default null,
  phone             varchar(11)     default null,
  email             varchar(50)     default null,
  status            char(1)         default '0',
  del_flag          char(1)         default '0',
  create_by         varchar(64)     default '',
  create_time       timestamp,
  update_by         varchar(64)     default '',
  update_time       timestamp,
  primary key (dept_id)
);
comment on table sys_dept is '部门表';
comment on column sys_dept.dept_id is '部门id';
comment on column sys_dept.parent_id is '父部门id';
-- ...（其余列注释）
```

- [x] **Step 2: 转换初始化 insert 语句**

`insert into ... values(...)` 基本保留，仅把值中的 `sysdate()` → `now()`。显式插入 id 的语句保持原 id 不变（序列在 Step 3 修正）。

示例：
```sql
insert into sys_dept values(100, 0, '0', '若依科技', 0, '若依', '15888888888', 'ry@qq.com', '0', '0', 'admin', now(), '', null);
```

- [x] **Step 3: 脚本末尾追加序列重置**

对所有「使用 bigserial/serial 且初始化数据显式插入了 id」的表，追加 setval（仅对实际有初始数据的表）：
```sql
-- 重置自增序列，避免与初始化数据 id 冲突
SELECT setval('sys_dept_dept_id_seq',      (SELECT max(dept_id)   FROM sys_dept));
SELECT setval('sys_user_user_id_seq',      (SELECT max(user_id)   FROM sys_user));
SELECT setval('sys_post_post_id_seq',      (SELECT max(post_id)   FROM sys_post));
SELECT setval('sys_role_role_id_seq',      (SELECT max(role_id)   FROM sys_role));
SELECT setval('sys_menu_menu_id_seq',      (SELECT max(menu_id)   FROM sys_menu));
SELECT setval('sys_dict_type_dict_id_seq', (SELECT max(dict_id)   FROM sys_dict_type));
SELECT setval('sys_dict_data_dict_code_seq',(SELECT max(dict_code) FROM sys_dict_data));
SELECT setval('sys_config_config_id_seq',  (SELECT max(config_id) FROM sys_config));
SELECT setval('sys_notice_notice_id_seq',  (SELECT max(notice_id) FROM sys_notice));
```
> 实际表名/列名以转换后的建表为准；序列默认名为 `<table>_<column>_seq`。对无初始数据的表（如 sys_oper_log、sys_logininfor）不需 setval。

- [x] **Step 4: 在 PostgreSQL 中执行脚本验证**

前置：本地有 PostgreSQL，已创建数据库 `ry-vue`。
Run: `psql -h localhost -U postgres -d ry-vue -v ON_ERROR_STOP=1 -f sql/ry_postgresql.sql`
Expected: 无 ERROR；所有 CREATE TABLE / INSERT / setval 成功执行。

> 已在临时库 `trainmind_verify_codex` 执行通过；未直接写入现有 `ruoyi` 数据库。

- [x] **Step 5: 静态检查无 MySQL 残留语法**

Run: `grep -niE 'auto_increment|engine=|`|sysdate\(\)|tinyint|datetime|int\([0-9]' sql/ry_postgresql.sql`
Expected: 无输出（退出码 1）。

- [x] **Step 6: Commit**

```bash
git add sql/ry_postgresql.sql
git commit -m "feat(sql): 新增 PostgreSQL 版建表与初始化脚本"
```

---

## Task 8: 生成 PG Quartz 脚本 `sql/quartz_postgresql.sql`

**Files:**
- Create: `sql/quartz_postgresql.sql`
- Reference: `sql/quartz.sql`（MySQL 源，173 行，QRTZ_* 表）

- [x] **Step 1: 采用官方 Quartz PG 建表脚本结构**

Quartz 官方提供 PostgreSQL 专用 DDL（`tables_postgres.sql`）。按其结构转换本项目 `quartz.sql` 中的 `QRTZ_*` 表：
- `blob` 类型 → `bytea`（PG 存储二进制 job data）。
- `bigint`/`int` → `int8`/`int4`。
- `datetime`/数字时间戳列保持 `bigint`（Quartz 用 epoch 毫秒）。
- 删除 `engine=innodb`、表内联 comment。
- 保留原有的 `QRTZ_` 表前缀与主外键约束。

关键差异表 `qrtz_job_details` / `qrtz_triggers` / `qrtz_blob_triggers` 中的 `job_data` / `blob_data` 列用 `bytea`。

- [x] **Step 2: 保留末尾初始化 insert（若有）**

`quartz.sql` 末尾若有 `commit;` 或初始数据，按 PG 语法保留（PG 支持 `commit;`，但脚本中多为 DDL，通常无需显式提交）。

- [x] **Step 3: 在 PostgreSQL 中执行脚本验证**

Run: `psql -h localhost -U postgres -d ry-vue -v ON_ERROR_STOP=1 -f sql/quartz_postgresql.sql`
Expected: 无 ERROR；所有 QRTZ_* 表创建成功。
> 已在临时库 `trainmind_verify_codex` 执行通过；未直接写入现有 `ruoyi` 数据库。

- [x] **Step 4: 静态检查无 MySQL 残留语法**

Run: `grep -niE 'auto_increment|engine=|`|tinyint|datetime' sql/quartz_postgresql.sql`
Expected: 无输出（退出码 1）。

补充检查：确认不存在 MySQL `blob` 类型定义，`job_data` / `blob_data` / `calendar` 均为 `bytea`。注意 `QRTZ_BLOB_TRIGGERS` 表名和 `blob_data` 列名是 Quartz 固有命名，不代表 MySQL `blob` 类型残留。

- [x] **Step 5: Commit**

```bash
git add sql/quartz_postgresql.sql
git commit -m "feat(sql): 新增 PostgreSQL 版 Quartz 建表脚本"
```

---

## Task 9: 整体编译 + 启动冒烟验证

**Files:** 无（验证任务）

- [x] **Step 1: 全量编译**

Run: `mvn -q clean compile`
Expected: BUILD SUCCESS。

- [ ] **Step 2: 启动应用（需已建库并执行两个 PG 脚本）**

Run: `mvn -pl ruoyi-admin spring-boot:run`（或运行 `RuoYiApplication`）
Expected: 控制台打印若依启动 banner，无数据源连接异常、无 Druid wall 拦截异常、无 MyBatis SQL 语法异常。

- [ ] **Step 3: 核心功能冒烟（手动，前端或 API）**

逐项确认（任一失败则回到对应 Task 修复）：
- [ ] 登录 admin/admin123 成功（验证 SysUser 查询 + now() 更新登录时间）。
- [ ] 用户管理列表，带创建时间范围筛选查询正常（验证 to_char）。
- [ ] 部门管理树正常加载；按部门查询用户正常（验证 ANY(string_to_array)）。
- [ ] 菜单/路由正常加载（验证 "query" 双引号 + coalesce）。
- [ ] 新增一个字典/部门后再新增一个，主键不冲突（验证 bigserial 序列 setval 正确）。

- [ ] **Step 4: 更新设计文档遗留项状态（如适用）**

若冒烟中发现新的 PG 兼容问题，记录到设计文档「已知遗留项」并视情况补任务。

- [ ] **Step 5: 最终提交（如有文档更新）**

```bash
git add -A
git commit -m "docs: 记录 PostgreSQL 迁移冒烟验证结果"
```

---

## 自检对照（spec coverage）

- 设计 §2.1 依赖 → Task 1 ✅
- 设计 §2.2 数据源 → Task 2 ✅
- 设计 §3.1 sysdate → Task 3 ✅
- 设计 §3.2 ifnull + §3.3 query → Task 4 ✅
- 设计 §3.4 find_in_set → Task 5 ✅
- 设计 §3.5 date_format → Task 6 ✅
- 设计 §4 ry 脚本 → Task 7 ✅
- 设计 §4 quartz 脚本 → Task 8 ✅
- 设计 §5 测试验证 → Task 9 ✅
- 设计 §6 生成器遗留 → 不在范围内，文档已标注 ✅
