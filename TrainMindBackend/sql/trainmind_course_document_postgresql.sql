-- ----------------------------
-- TrainMind 课程资料上传与文件服务（PostgreSQL）
-- 适用 PostgreSQL 12+
-- 说明：本脚本为业务迁移脚本，不删除已有业务数据。
-- ----------------------------

-- ----------------------------
-- 1、课程表
-- ----------------------------
create table if not exists course (
  id                bigserial       not null,
  tenant_id         int8            default 1 not null,
  course_code       varchar(64)     default '',
  course_name       varchar(200)    not null,
  course_category   varchar(100)    default '',
  description       varchar(1000)   default null,
  owner_user_id     int8            default null,
  start_date        date            default null,
  allow_download    boolean         default false not null,
  status            varchar(20)     default 'draft' not null,
  sort_order        int4            default 0,
  del_flag          char(1)         default '0',
  create_by         varchar(64)     default '',
  create_time       timestamp,
  update_by         varchar(64)     default '',
  update_time       timestamp,
  remark            varchar(500)    default null,
  primary key (id)
);

alter table course
  add column if not exists course_category varchar(100) default '',
  add column if not exists start_date date default null,
  add column if not exists allow_download boolean default false not null;

comment on table course                  is '课程表';
comment on column course.id              is '课程ID';
comment on column course.tenant_id       is '租户ID';
comment on column course.course_code     is '课程编码';
comment on column course.course_name     is '课程名称';
comment on column course.course_category is '课程分类';
comment on column course.description     is '课程简介';
comment on column course.owner_user_id   is '课程讲师或负责人用户ID';
comment on column course.start_date      is '开课日期';
comment on column course.allow_download  is '是否允许学员下载当前已发布资料';
comment on column course.status          is '课程状态（draft草稿 active正常 disabled停用 archived归档）';
comment on column course.sort_order      is '显示顺序';
comment on column course.del_flag        is '删除标志（0代表存在 2代表删除）';
comment on column course.create_by       is '创建者';
comment on column course.create_time     is '创建时间';
comment on column course.update_by       is '更新者';
comment on column course.update_time     is '更新时间';
comment on column course.remark          is '备注';

create unique index if not exists uk_course_code_alive on course(tenant_id, course_code) where del_flag = '0' and course_code <> '';
create index if not exists idx_course_owner on course(tenant_id, owner_user_id, del_flag);
create index if not exists idx_course_status on course(tenant_id, status, del_flag, sort_order);

-- ----------------------------
-- 2、课程模块表
-- ----------------------------
create table if not exists course_module (
  id                bigserial       not null,
  tenant_id         int8            default 1 not null,
  course_id         int8            not null,
  module_code       varchar(64)     default '',
  module_name       varchar(200)    not null,
  description       varchar(1000)   default null,
  sort_order        int4            default 0,
  status            varchar(20)     default 'active' not null,
  del_flag          char(1)         default '0',
  create_by         varchar(64)     default '',
  create_time       timestamp,
  update_by         varchar(64)     default '',
  update_time       timestamp,
  remark            varchar(500)    default null,
  primary key (id)
);
comment on table course_module                  is '课程模块表';
comment on column course_module.id              is '课程模块ID';
comment on column course_module.tenant_id       is '租户ID';
comment on column course_module.course_id       is '课程ID';
comment on column course_module.module_code     is '模块编码，例如M1';
comment on column course_module.module_name     is '模块名称';
comment on column course_module.description     is '模块说明';
comment on column course_module.sort_order      is '显示顺序';
comment on column course_module.status          is '模块状态（active正常 disabled停用）';
comment on column course_module.del_flag        is '删除标志（0代表存在 2代表删除）';
comment on column course_module.create_by       is '创建者';
comment on column course_module.create_time     is '创建时间';
comment on column course_module.update_by       is '更新者';
comment on column course_module.update_time     is '更新时间';
comment on column course_module.remark          is '备注';

create unique index if not exists uk_course_module_code_alive on course_module(tenant_id, course_id, module_code) where del_flag = '0' and module_code <> '';
create index if not exists idx_course_module_course on course_module(tenant_id, course_id, del_flag, sort_order);
create index if not exists idx_course_module_status on course_module(tenant_id, status, del_flag);

-- ----------------------------
-- 3、课程资料表
-- ----------------------------
create table if not exists course_document (
  id                 bigserial       not null,
  tenant_id          int8            default 1 not null,
  course_id          int8            not null,
  module_id          int8            default null,
  title              varchar(255)    not null,
  document_type      varchar(20)     default '',
  latest_version_id  int8            default null,
  status             varchar(20)     default 'active' not null,
  del_flag           char(1)         default '0',
  create_by          varchar(64)     default '',
  create_time        timestamp,
  update_by          varchar(64)     default '',
  update_time        timestamp,
  remark             varchar(500)    default null,
  primary key (id)
);
comment on table course_document                    is '课程资料表';
comment on column course_document.id                is '资料ID';
comment on column course_document.tenant_id         is '租户ID';
comment on column course_document.course_id         is '课程ID';
comment on column course_document.module_id         is '课程模块ID，空表示课程公共资料';
comment on column course_document.title             is '资料标题';
comment on column course_document.document_type     is '资料类型，第一阶段可等于文件扩展名';
comment on column course_document.latest_version_id is '最新资料版本ID';
comment on column course_document.status            is '资料状态（active正常 archived归档）';
comment on column course_document.del_flag          is '删除标志（0代表存在 2代表删除）';
comment on column course_document.create_by         is '创建者';
comment on column course_document.create_time       is '创建时间';
comment on column course_document.update_by         is '更新者';
comment on column course_document.update_time       is '更新时间';
comment on column course_document.remark            is '备注';

create index if not exists idx_course_document_course_module on course_document(tenant_id, course_id, module_id, status, del_flag);
create index if not exists idx_course_document_latest_version on course_document(latest_version_id);
create index if not exists idx_course_document_title on course_document(tenant_id, course_id, title);

-- ----------------------------
-- 4、课程资料版本表
-- ----------------------------
-- 兼容已执行旧版脚本的数据库。
do $$
begin
  if to_regclass('public.course_document_version') is not null
     and exists (
       select 1 from information_schema.columns
       where table_schema = 'public'
         and table_name = 'course_document_version'
         and column_name = 'parse_status'
     )
     and not exists (
       select 1 from information_schema.columns
       where table_schema = 'public'
         and table_name = 'course_document_version'
         and column_name = 'status'
     ) then
    alter table course_document_version rename column parse_status to status;
  end if;
end $$;

create table if not exists course_document_version (
  id                   bigserial       not null,
  tenant_id            int8            default 1 not null,
  course_id            int8            not null,
  module_id            int8            default null,
  document_id          int8            not null,
  version_no           int4            not null,
  original_filename    varchar(255)    not null,
  file_ext             varchar(20)     not null,
  content_type         varchar(100)    default '',
  file_size            int8            default 0 not null,
  checksum_md5         varchar(32)     default '',
  bucket               varchar(100)    default '',
  object_name          varchar(1000)   default '',
  status               varchar(20)     default 'uploaded' not null,
  parse_task_id        int8            default null,
  parse_error_message  varchar(1000)   default null,
  del_flag             char(1)         default '0',
  create_by            varchar(64)     default '',
  create_time          timestamp,
  update_by            varchar(64)     default '',
  update_time          timestamp,
  remark               varchar(500)    default null,
  primary key (id)
);

alter table course_document_version
  add column if not exists update_by varchar(64) default '',
  add column if not exists update_time timestamp;

update course_document_version
set status = 'failed'
where status = 'parse_failed';

alter table course_document_version
  alter column status set default 'uploaded';

comment on table course_document_version                       is '课程资料版本表';
comment on column course_document_version.id                   is '资料版本ID';
comment on column course_document_version.tenant_id            is '租户ID';
comment on column course_document_version.course_id            is '课程ID';
comment on column course_document_version.module_id            is '课程模块ID，空表示课程公共资料';
comment on column course_document_version.document_id          is '资料ID';
comment on column course_document_version.version_no           is '版本号，从1递增';
comment on column course_document_version.original_filename    is '原始文件名';
comment on column course_document_version.file_ext             is '文件扩展名';
comment on column course_document_version.content_type         is 'MIME类型';
comment on column course_document_version.file_size            is '文件大小，单位字节';
comment on column course_document_version.checksum_md5         is '文件MD5';
comment on column course_document_version.bucket               is '对象存储Bucket';
comment on column course_document_version.object_name          is '对象存储Key';
comment on column course_document_version.status               is '资料版本状态（uploaded待解析 parsing解析中 parsed已解析 failed失败 archived归档）';
comment on column course_document_version.parse_task_id        is 'AI解析任务ID';
comment on column course_document_version.parse_error_message  is '解析失败原因';
comment on column course_document_version.del_flag             is '删除标志（0代表存在 2代表删除）';
comment on column course_document_version.create_by            is '上传者';
comment on column course_document_version.create_time          is '上传时间';
comment on column course_document_version.update_by            is '更新者';
comment on column course_document_version.update_time          is '更新时间';
comment on column course_document_version.remark               is '备注';

create unique index if not exists uk_doc_version_no on course_document_version(tenant_id, document_id, version_no);
create index if not exists idx_doc_version_document on course_document_version(tenant_id, document_id, del_flag, id desc);
drop index if exists idx_doc_version_parse_status;
create index if not exists idx_doc_version_status on course_document_version(tenant_id, status, del_flag);
create index if not exists idx_doc_version_object on course_document_version(bucket, object_name);
create index if not exists idx_doc_version_course_module on course_document_version(tenant_id, course_id, module_id, del_flag);

-- ----------------------------
-- 5、文档解析任务表
-- ----------------------------
create table if not exists document_parse_task (
  id                   bigserial       not null,
  tenant_id            int8            default 1 not null,
  document_id          int8            not null,
  document_version_id  int8            not null,
  status               varchar(20)     default 'pending' not null,
  current_step         varchar(64)     default null,
  progress             int4            default 0 not null,
  error_code           varchar(64)     default null,
  error_message        varchar(1000)   default null,
  retry_count          int4            default 0 not null,
  payload_json         jsonb           default '{}'::jsonb not null,
  started_at           timestamp       default null,
  finished_at          timestamp       default null,
  del_flag             char(1)         default '0',
  create_by            varchar(64)     default '',
  create_time          timestamp,
  update_by            varchar(64)     default '',
  update_time          timestamp,
  remark               varchar(500)    default null,
  primary key (id)
);
alter table document_parse_task
  add column if not exists payload_json jsonb default '{}'::jsonb not null;

comment on table document_parse_task                     is '文档解析任务表';
comment on column document_parse_task.id                 is '解析任务ID';
comment on column document_parse_task.tenant_id          is '租户ID';
comment on column document_parse_task.document_id        is '资料ID';
comment on column document_parse_task.document_version_id is '资料版本ID';
comment on column document_parse_task.status             is '任务状态（pending等待 running执行中 success成功 failed失败 cancelled取消）';
comment on column document_parse_task.current_step       is '当前处理步骤';
comment on column document_parse_task.progress           is '处理进度百分比';
comment on column document_parse_task.error_code         is '错误码';
comment on column document_parse_task.error_message      is '错误信息';
comment on column document_parse_task.retry_count        is '重试次数';
comment on column document_parse_task.payload_json       is '解析任务请求快照';
comment on column document_parse_task.started_at         is '开始时间';
comment on column document_parse_task.finished_at        is '结束时间';
comment on column document_parse_task.del_flag           is '删除标志（0代表存在 2代表删除）';
comment on column document_parse_task.create_by          is '创建者';
comment on column document_parse_task.create_time        is '创建时间';
comment on column document_parse_task.update_by          is '更新者';
comment on column document_parse_task.update_time        is '更新时间';
comment on column document_parse_task.remark             is '备注';

create index if not exists idx_parse_task_version on document_parse_task(tenant_id, document_version_id, del_flag, id desc);
create index if not exists idx_parse_task_status on document_parse_task(tenant_id, status, del_flag, create_time);
create unique index if not exists uk_parse_task_active_version
  on document_parse_task(tenant_id, document_version_id)
  where del_flag = '0' and status in ('pending', 'running');

-- ----------------------------
-- 6、状态字典
-- ----------------------------
-- 清理旧版解析状态字典，迁移为统一资料版本状态字典。
delete from sys_dict_data where dict_type = 'trainmind_document_parse_status';
delete from sys_dict_type where dict_type = 'trainmind_document_parse_status';

insert into sys_dict_type(dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
values
  ('课程状态', 'trainmind_course_status', '0', 'admin', now(), '', null, 'TrainMind课程状态'),
  ('课程模块状态', 'trainmind_course_module_status', '0', 'admin', now(), '', null, 'TrainMind课程模块状态'),
  ('课程资料状态', 'trainmind_course_document_status', '0', 'admin', now(), '', null, 'TrainMind课程资料状态'),
  ('资料版本状态', 'trainmind_document_version_status', '0', 'admin', now(), '', null, 'TrainMind资料版本状态'),
  ('文档解析任务状态', 'trainmind_document_parse_task_status', '0', 'admin', now(), '', null, 'TrainMind文档解析任务状态')
on conflict (dict_type) do update
set dict_name = excluded.dict_name,
    status = excluded.status,
    update_by = 'admin',
    update_time = now(),
    remark = excluded.remark;

-- 只重建本业务字典数据，避免重复执行脚本产生重复字典项。
delete from sys_dict_data
where dict_type in (
  'trainmind_course_status',
  'trainmind_course_module_status',
  'trainmind_course_document_status',
  'trainmind_document_version_status',
  'trainmind_document_parse_task_status'
);

insert into sys_dict_data(dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
values
  (1, '草稿', 'draft', 'trainmind_course_status', '', 'info', 'Y', '0', 'admin', now(), '', null, '课程草稿'),
  (2, '正常', 'active', 'trainmind_course_status', '', 'success', 'N', '0', 'admin', now(), '', null, '课程正常'),
  (3, '停用', 'disabled', 'trainmind_course_status', '', 'danger', 'N', '0', 'admin', now(), '', null, '课程停用'),
  (4, '归档', 'archived', 'trainmind_course_status', '', 'info', 'N', '0', 'admin', now(), '', null, '课程归档'),

  (1, '正常', 'active', 'trainmind_course_module_status', '', 'success', 'Y', '0', 'admin', now(), '', null, '课程模块正常'),
  (2, '停用', 'disabled', 'trainmind_course_module_status', '', 'danger', 'N', '0', 'admin', now(), '', null, '课程模块停用'),

  (1, '正常', 'active', 'trainmind_course_document_status', '', 'success', 'Y', '0', 'admin', now(), '', null, '课程资料正常'),
  (2, '归档', 'archived', 'trainmind_course_document_status', '', 'info', 'N', '0', 'admin', now(), '', null, '课程资料归档'),

  (1, '待解析', 'uploaded', 'trainmind_document_version_status', '', 'info', 'Y', '0', 'admin', now(), '', null, '资料已上传待解析'),
  (2, '解析中', 'parsing', 'trainmind_document_version_status', '', 'warning', 'N', '0', 'admin', now(), '', null, '资料解析中'),
  (3, '已解析', 'parsed', 'trainmind_document_version_status', '', 'success', 'N', '0', 'admin', now(), '', null, '资料已解析'),
  (4, '失败', 'failed', 'trainmind_document_version_status', '', 'danger', 'N', '0', 'admin', now(), '', null, '资料处理失败'),
  (5, '已归档', 'archived', 'trainmind_document_version_status', '', 'info', 'N', '0', 'admin', now(), '', null, '资料版本已归档'),

  (1, '等待中', 'pending', 'trainmind_document_parse_task_status', '', 'info', 'Y', '0', 'admin', now(), '', null, '解析任务等待执行'),
  (2, '执行中', 'running', 'trainmind_document_parse_task_status', '', 'warning', 'N', '0', 'admin', now(), '', null, '解析任务执行中'),
  (3, '成功', 'success', 'trainmind_document_parse_task_status', '', 'success', 'N', '0', 'admin', now(), '', null, '解析任务执行成功'),
  (4, '失败', 'failed', 'trainmind_document_parse_task_status', '', 'danger', 'N', '0', 'admin', now(), '', null, '解析任务执行失败'),
  (5, '已取消', 'cancelled', 'trainmind_document_parse_task_status', '', 'info', 'N', '0', 'admin', now(), '', null, '解析任务已取消');
