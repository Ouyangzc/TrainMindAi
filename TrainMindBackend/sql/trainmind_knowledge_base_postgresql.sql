-- TrainMind 知识库治理（PostgreSQL 12+）
-- 前置：trainmind_course_document_postgresql.sql
-- 本脚本可重复执行，不删除已有业务数据。

create table if not exists knowledge_base (
  id bigserial primary key,
  tenant_id int8 default 1 not null,
  course_id int8 not null,
  name varchar(255) not null,
  description varchar(1000),
  current_version_id int8,
  status varchar(20) default 'active' not null,
  del_flag char(1) default '0' not null,
  create_by varchar(64) default '',
  create_time timestamp,
  update_by varchar(64) default '',
  update_time timestamp,
  remark varchar(500)
);
comment on table knowledge_base is '课程知识库表';
comment on column knowledge_base.course_id is '课程ID，MVP一门课程唯一对应一个知识库';
comment on column knowledge_base.current_version_id is '当前已发布知识库版本ID';
comment on column knowledge_base.status is '状态（active正常 archived归档）';
comment on column knowledge_base.del_flag is '删除标志（0存在 2删除）';
create unique index if not exists uk_knowledge_base_course_alive
  on knowledge_base(tenant_id, course_id) where del_flag = '0';
create index if not exists idx_knowledge_base_current_version
  on knowledge_base(current_version_id) where del_flag = '0';

create table if not exists knowledge_base_version (
  id bigserial primary key,
  tenant_id int8 default 1 not null,
  knowledge_base_id int8 not null,
  version_no int4 not null,
  status varchar(20) default 'draft' not null,
  chunk_count int4 default 0 not null,
  chunk_strategy_version varchar(32) not null,
  retrieval_strategy_version varchar(32) not null,
  embedding_index_version_id int8,
  keyword_index_version_id int8,
  build_task_id int8,
  build_error_message varchar(1000),
  published_at timestamp,
  published_by varchar(64),
  del_flag char(1) default '0' not null,
  create_by varchar(64) default '',
  create_time timestamp,
  update_by varchar(64) default '',
  update_time timestamp,
  remark varchar(500)
);
alter table knowledge_base_version
  add column if not exists build_task_id int8,
  add column if not exists build_error_message varchar(1000);
comment on table knowledge_base_version is '知识库版本表';
comment on column knowledge_base_version.version_no is '知识库内递增版本号';
comment on column knowledge_base_version.status is '状态（draft building ready published failed archived）';
comment on column knowledge_base_version.chunk_strategy_version is '本版本固定的切分策略版本';
comment on column knowledge_base_version.retrieval_strategy_version is '本版本固定的检索策略版本';
comment on column knowledge_base_version.embedding_index_version_id is 'AI向量索引版本ID';
comment on column knowledge_base_version.keyword_index_version_id is 'AI关键词索引版本ID';
comment on column knowledge_base_version.build_task_id is '最近一次AI构建任务ID';
comment on column knowledge_base_version.build_error_message is '最近一次构建失败原因';
comment on column knowledge_base_version.del_flag is '删除标志（0存在 2删除）';
create unique index if not exists uk_kb_version_no_alive
  on knowledge_base_version(tenant_id, knowledge_base_id, version_no) where del_flag = '0';
create unique index if not exists uk_kb_version_single_active
  on knowledge_base_version(tenant_id, knowledge_base_id)
  where del_flag = '0' and status in ('draft', 'building', 'ready', 'failed');
create index if not exists idx_kb_version_history
  on knowledge_base_version(tenant_id, knowledge_base_id, del_flag, version_no desc);
create index if not exists idx_kb_version_status
  on knowledge_base_version(tenant_id, status, del_flag);

create table if not exists knowledge_base_version_document (
  id bigserial primary key,
  tenant_id int8 default 1 not null,
  knowledge_base_version_id int8 not null,
  document_id int8 not null,
  document_version_id int8 not null,
  del_flag char(1) default '0' not null,
  create_by varchar(64) default '',
  create_time timestamp,
  update_by varchar(64) default '',
  update_time timestamp,
  remark varchar(500)
);
comment on table knowledge_base_version_document is '知识库版本资料快照表';
comment on column knowledge_base_version_document.knowledge_base_version_id is '知识库版本ID';
comment on column knowledge_base_version_document.document_id is '资料ID，同一知识库版本内唯一';
comment on column knowledge_base_version_document.document_version_id is '纳入快照的具体资料版本ID';
comment on column knowledge_base_version_document.del_flag is '删除标志（0存在 2删除）';
create unique index if not exists uk_kb_version_document_alive
  on knowledge_base_version_document(tenant_id, knowledge_base_version_id, document_id)
  where del_flag = '0';
create index if not exists idx_kb_version_document_version
  on knowledge_base_version_document(tenant_id, document_version_id, del_flag);
create index if not exists idx_kb_version_document_snapshot
  on knowledge_base_version_document(tenant_id, knowledge_base_version_id, del_flag);

create table if not exists course_user (
  id bigserial primary key,
  tenant_id int8 default 1 not null,
  course_id int8 not null,
  user_id int8 not null,
  access_role varchar(20) not null,
  access_status varchar(20) default 'active' not null,
  start_at timestamp,
  end_at timestamp,
  del_flag char(1) default '0' not null,
  create_by varchar(64) default '',
  create_time timestamp,
  update_by varchar(64) default '',
  update_time timestamp,
  remark varchar(500)
);
comment on table course_user is '课程用户直接授权表';
comment on column course_user.access_role is '课程角色（owner teacher student）';
comment on column course_user.access_status is '授权状态（active disabled）';
comment on column course_user.start_at is '授权生效时间，空表示立即生效';
comment on column course_user.end_at is '授权失效时间，空表示长期有效';
comment on column course_user.del_flag is '删除标志（0存在 2删除）';
create unique index if not exists uk_course_user_alive
  on course_user(tenant_id, course_id, user_id) where del_flag = '0';
create unique index if not exists uk_course_owner_active
  on course_user(tenant_id, course_id)
  where del_flag = '0' and access_role = 'owner' and access_status = 'active';
create index if not exists idx_course_user_access
  on course_user(tenant_id, user_id, access_status, del_flag, course_id);

-- 兼容迁移前已有课程：以 course.owner_user_id 为准补齐负责人直接授权。
-- 若课程已经存在其他活动负责人，则保留现有授权，交由负责人转移功能处理。
update course_user cu
set access_role = 'owner',
    access_status = 'active',
    update_by = 'migration',
    update_time = now()
from course c
where c.del_flag = '0'
  and c.owner_user_id is not null
  and cu.tenant_id = c.tenant_id
  and cu.course_id = c.id
  and cu.user_id = c.owner_user_id
  and cu.del_flag = '0'
  and not exists (
    select 1
    from course_user existing_owner
    where existing_owner.tenant_id = c.tenant_id
      and existing_owner.course_id = c.id
      and existing_owner.access_role = 'owner'
      and existing_owner.access_status = 'active'
      and existing_owner.del_flag = '0'
      and existing_owner.id <> cu.id
  );

insert into course_user(
  tenant_id, course_id, user_id, access_role, access_status,
  del_flag, create_by, create_time, update_by, update_time, remark
)
select
  c.tenant_id, c.id, c.owner_user_id, 'owner', 'active',
  '0', 'migration', now(), '', null, '由课程负责人字段迁移生成'
from course c
where c.del_flag = '0'
  and c.owner_user_id is not null
  and not exists (
    select 1
    from course_user cu
    where cu.tenant_id = c.tenant_id
      and cu.course_id = c.id
      and cu.user_id = c.owner_user_id
      and cu.del_flag = '0'
  )
  and not exists (
    select 1
    from course_user existing_owner
    where existing_owner.tenant_id = c.tenant_id
      and existing_owner.course_id = c.id
      and existing_owner.access_role = 'owner'
      and existing_owner.access_status = 'active'
      and existing_owner.del_flag = '0'
  );

insert into sys_dict_type(
  dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark
)
values
  ('知识库版本状态', 'trainmind_knowledge_base_version_status', '0', 'admin', now(), '', null, 'TrainMind知识库版本状态'),
  ('课程授权角色', 'trainmind_course_access_role', '0', 'admin', now(), '', null, 'TrainMind课程直接授权角色'),
  ('课程授权状态', 'trainmind_course_access_status', '0', 'admin', now(), '', null, 'TrainMind课程直接授权状态')
on conflict (dict_type) do update
set dict_name = excluded.dict_name,
    status = excluded.status,
    update_by = 'admin',
    update_time = now(),
    remark = excluded.remark;

delete from sys_dict_data
where dict_type in (
  'trainmind_knowledge_base_version_status',
  'trainmind_course_access_role',
  'trainmind_course_access_status'
);

insert into sys_dict_data(
  dict_sort, dict_label, dict_value, dict_type, css_class, list_class,
  is_default, status, create_by, create_time, update_by, update_time, remark
)
values
  (1, '草稿', 'draft', 'trainmind_knowledge_base_version_status', '', 'info', 'Y', '0', 'admin', now(), '', null, '知识库草稿'),
  (2, '构建中', 'building', 'trainmind_knowledge_base_version_status', '', 'warning', 'N', '0', 'admin', now(), '', null, '知识库正在构建'),
  (3, '待发布', 'ready', 'trainmind_knowledge_base_version_status', '', 'primary', 'N', '0', 'admin', now(), '', null, '知识库构建完成待发布'),
  (4, '已发布', 'published', 'trainmind_knowledge_base_version_status', '', 'success', 'N', '0', 'admin', now(), '', null, '当前发布版本'),
  (5, '构建失败', 'failed', 'trainmind_knowledge_base_version_status', '', 'danger', 'N', '0', 'admin', now(), '', null, '知识库构建失败'),
  (6, '已归档', 'archived', 'trainmind_knowledge_base_version_status', '', 'info', 'N', '0', 'admin', now(), '', null, '知识库历史版本'),
  (1, '主负责人', 'owner', 'trainmind_course_access_role', '', 'danger', 'N', '0', 'admin', now(), '', null, '课程唯一主负责人'),
  (2, '讲师', 'teacher', 'trainmind_course_access_role', '', 'primary', 'N', '0', 'admin', now(), '', null, '课程讲师'),
  (3, '学员', 'student', 'trainmind_course_access_role', '', 'info', 'Y', '0', 'admin', now(), '', null, '课程学员'),
  (1, '正常', 'active', 'trainmind_course_access_status', '', 'success', 'Y', '0', 'admin', now(), '', null, '授权有效'),
  (2, '停用', 'disabled', 'trainmind_course_access_status', '', 'danger', 'N', '0', 'admin', now(), '', null, '授权停用');
