-- TrainMind 学员端系统角色（课程数据权限仍由 course_user 决定）
insert into sys_role(role_name,role_key,role_sort,data_scope,menu_check_strictly,
  dept_check_strictly,status,del_flag,create_by,create_time,remark)
select '学员','student',30,'1',1,1,'0','0','system',now(),'学员学习空间路由角色'
where not exists (select 1 from sys_role where role_key='student' and del_flag='0');
