-- TrainMind 学员端事实活动记录（PostgreSQL 12+）
create table if not exists student_learning_activity (
  id            bigserial primary key,
  tenant_id     int8 not null default 1,
  user_id       int8 not null,
  course_id     int8 not null,
  activity_type varchar(32) not null,
  target_id     int8,
  target_title  varchar(255),
  target_detail varchar(500),
  occurred_at   timestamp not null default now(),
  metadata_json jsonb,
  del_flag      char(1) not null default '0',
  create_by     varchar(64) default '',
  create_time   timestamp not null default now(),
  update_by     varchar(64) default '',
  update_time   timestamp,
  remark        varchar(500),
  constraint ck_student_learning_activity_type
    check (activity_type in ('course_view', 'module_view', 'document_view', 'chat'))
);

comment on table student_learning_activity is '学员课程事实活动记录';
create index if not exists idx_student_activity_user_course
  on student_learning_activity(tenant_id, user_id, course_id, del_flag, occurred_at desc, id desc);
create index if not exists idx_student_activity_dedupe
  on student_learning_activity(tenant_id, user_id, course_id, activity_type, target_id, occurred_at desc);
