-- TrainMind 学员课程问答会话（PostgreSQL 12+）
-- 业务会话位于 public schema；AI 检索与模型日志位于 ai schema。

create table if not exists qa_session (
  id          bigserial primary key,
  tenant_id   int8 not null default 1,
  user_id     int8 not null,
  course_id   int8 not null,
  title       varchar(200) not null default '新对话',
  status      varchar(20) not null default 'active',
  del_flag    char(1) not null default '0',
  create_by   varchar(64) default '',
  create_time timestamp not null default now(),
  update_by   varchar(64) default '',
  update_time timestamp,
  remark      varchar(500)
);

comment on table qa_session is '学员课程AI问答会话';
create index if not exists idx_qa_session_user_course
  on qa_session(tenant_id, user_id, course_id, del_flag, update_time desc, id desc);

create table if not exists qa_message (
  id                         bigserial primary key,
  tenant_id                  int8 not null default 1,
  session_id                 int8 not null,
  user_id                    int8 not null,
  course_id                  int8 not null,
  knowledge_base_version_id  int8 not null,
  role                       varchar(20) not null,
  content                    text not null default '',
  status                     varchar(32) not null default 'completed',
  reject_reason              varchar(64),
  retrieval_log_ref          int8,
  del_flag                   char(1) not null default '0',
  create_by                  varchar(64) default '',
  create_time                timestamp not null default now(),
  update_by                  varchar(64) default '',
  update_time                timestamp,
  remark                     varchar(500),
  constraint ck_qa_message_role check (role in ('user', 'assistant')),
  constraint ck_qa_message_status check (status in ('pending', 'grounded', 'insufficient_evidence', 'service_unavailable', 'completed'))
);

comment on table qa_message is '学员课程AI问答消息';
create index if not exists idx_qa_message_session
  on qa_message(tenant_id, session_id, del_flag, id);
create index if not exists idx_qa_message_kb_version
  on qa_message(knowledge_base_version_id, del_flag);

create table if not exists qa_message_citation (
  id                   bigserial primary key,
  tenant_id            int8 not null default 1,
  message_id           int8 not null,
  chunk_id             int8,
  document_id          int8 not null,
  document_version_id  int8 not null,
  document_title       varchar(255) not null,
  version_no           int4,
  source_file          varchar(512),
  page_start           int4,
  page_end             int4,
  section_title        varchar(512),
  quote                text,
  score                numeric(10,8),
  rank_no              int4,
  del_flag             char(1) not null default '0',
  create_by            varchar(64) default '',
  create_time          timestamp not null default now(),
  update_by            varchar(64) default '',
  update_time          timestamp,
  remark               varchar(500)
);

comment on table qa_message_citation is 'AI回答的结构化资料引用快照';
create index if not exists idx_qa_citation_message
  on qa_message_citation(tenant_id, message_id, del_flag, rank_no, id);
create index if not exists idx_qa_citation_document_version
  on qa_message_citation(document_version_id, del_flag);
