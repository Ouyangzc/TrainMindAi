-- 学员端验收夹具。账号 student_accept_a / student_accept_b，密码 admin123。
-- 使用 9100 段固定 ID，可重复执行，不覆盖现有业务行。

\ir trainmind_student_role_postgresql.sql

insert into sys_user(user_id,dept_id,user_name,nick_name,user_type,email,phonenumber,sex,
  password,status,del_flag,create_by,create_time,remark)
values
  (9101,103,'student_accept_a','验收学员A','00','','','0',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2','0','0','system',now(),'学员端验收夹具'),
  (9102,103,'student_accept_b','验收学员B','00','','','0',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2','0','0','system',now(),'学员端验收夹具')
on conflict (user_id) do update set status='0',del_flag='0';

insert into sys_user_role(user_id,role_id)
select u.user_id,r.role_id from sys_user u cross join sys_role r
where u.user_id in (9101,9102) and r.role_key='student'
  and not exists(select 1 from sys_user_role ur where ur.user_id=u.user_id and ur.role_id=r.role_id);

insert into course(id,tenant_id,course_code,course_name,description,owner_user_id,status,
  sort_order,del_flag,create_by,create_time,course_category,allow_download)
values
  (9101,1,'ACCEPT-AVAILABLE','第二门可学习课程','用于验证多课程切换',1,'active',91,'0','system',now(),'验收数据',false),
  (9102,1,'ACCEPT-PREPARING','内容准备中课程','用于验证无发布版本状态',1,'active',92,'0','system',now(),'验收数据',false),
  (9103,1,'ACCEPT-EXPIRED','授权已到期课程','用于验证授权到期状态',1,'active',93,'0','system',now(),'验收数据',false),
  (9199,2,'ACCEPT-TENANT-2','其他租户课程','用于验证租户隔离',1,'active',99,'0','system',now(),'验收数据',false)
on conflict (id) do update set status=excluded.status,del_flag='0';

insert into knowledge_base(id,tenant_id,course_id,name,description,status,del_flag,create_by,create_time)
values (9101,1,9101,'第二门可学习课程知识库','空发布快照验收','active','0','system',now())
on conflict (id) do update set status='active',del_flag='0';

insert into knowledge_base_version(id,tenant_id,knowledge_base_id,version_no,status,chunk_count,
  chunk_strategy_version,retrieval_strategy_version,published_at,published_by,del_flag,create_by,create_time)
values
  (9101,1,9101,1,'published',0,'v1','v1',now(),'system','0','system',now()),
  (9102,1,1,2,'ready',0,'v1','v1',null,null,'0','system',now())
on conflict (id) do update set status=excluded.status,del_flag='0';

update knowledge_base set current_version_id=9101 where id=9101;

insert into course_user(id,tenant_id,course_id,user_id,access_role,access_status,start_at,end_at,
  del_flag,create_by,create_time,remark)
values
  (9101,1,1,9101,'student','active',now()-interval '1 day',now()+interval '30 days','0','system',now(),'学员A主课程'),
  (9102,1,9101,9101,'student','active',now()-interval '1 day',now()+interval '30 days','0','system',now(),'学员A第二课程'),
  (9103,1,9102,9101,'student','active',now()-interval '1 day',now()+interval '30 days','0','system',now(),'内容准备中'),
  (9104,1,9103,9101,'student','active',now()-interval '30 days',now()-interval '1 day','0','system',now(),'已到期'),
  (9105,1,1,9102,'student','active',now()-interval '1 day',now()+interval '30 days','0','system',now(),'学员B共享课程')
on conflict (id) do update set access_status=excluded.access_status,start_at=excluded.start_at,
  end_at=excluded.end_at,del_flag='0';
