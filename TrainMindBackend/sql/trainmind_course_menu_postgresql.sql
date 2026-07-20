-- TrainMind 课程管理菜单与按钮权限（PostgreSQL）
-- 本脚本可重复执行，不自动向普通角色授权。

select setval(
  pg_get_serial_sequence('sys_menu', 'menu_id'),
  greatest(coalesce((select max(menu_id) from sys_menu), 1), 1),
  true
);

do $$
declare
  course_menu_id int8;
begin
  select menu_id
    into course_menu_id
    from sys_menu
   where perms = 'course:course:list'
      or (parent_id = 0 and path = 'course' and menu_type = 'C')
   order by menu_id
   limit 1;

  if course_menu_id is null then
    insert into sys_menu(
      menu_name, parent_id, order_num, path, component, "query", route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) values (
      '课程管理', 0, 4, 'course', 'course/index', null, 'Course',
      1, 0, 'C', '0', '0', 'course:course:list', 'education',
      'admin', now(), '', null, '课程管理菜单'
    )
    returning menu_id into course_menu_id;
  else
    update sys_menu
       set menu_name = '课程管理',
           parent_id = 0,
           order_num = 4,
           path = 'course',
           component = 'course/index',
           route_name = 'Course',
           is_frame = 1,
           is_cache = 0,
           menu_type = 'C',
           visible = '0',
           status = '0',
           perms = 'course:course:list',
           icon = 'education',
           update_by = 'admin',
           update_time = now(),
           remark = '课程管理菜单'
     where menu_id = course_menu_id;
  end if;

  insert into sys_menu(
    menu_name, parent_id, order_num, path, component, "query", route_name,
    is_frame, is_cache, menu_type, visible, status, perms, icon,
    create_by, create_time, update_by, update_time, remark
  )
  select permission_name, course_menu_id, permission_order, '', '', null, '',
         1, 0, 'F', '0', '0', permission_code, '#',
         'admin', now(), '', null, ''
    from (values
      ('课程查询',       1,  'course:course:query'),
      ('课程新增',       2,  'course:course:add'),
      ('课程修改',       3,  'course:course:edit'),
      ('课程删除',       4,  'course:course:remove'),
      ('模块列表',       10, 'course:module:list'),
      ('模块查询',       11, 'course:module:query'),
      ('模块新增',       12, 'course:module:add'),
      ('模块修改',       13, 'course:module:edit'),
      ('模块删除',       14, 'course:module:remove'),
      ('资料列表',       20, 'course:document:list'),
      ('资料查询',       21, 'course:document:query'),
      ('资料上传',       22, 'course:document:upload'),
      ('资料下载',       23, 'course:document:download'),
      ('资料解析',       24, 'course:document:parse'),
      ('资料删除',       25, 'course:document:remove'),
      ('知识库查询',     30, 'course:knowledge-base:query'),
      ('知识库编辑',     31, 'course:knowledge-base:edit'),
      ('知识库构建',     32, 'course:knowledge-base:build'),
      ('知识库发布',     33, 'course:knowledge-base:publish'),
      ('课程成员列表',   40, 'course:member:list'),
      ('课程成员管理',   41, 'course:member:edit')
    ) as permissions(permission_name, permission_order, permission_code)
   where not exists (
     select 1
       from sys_menu existing
      where existing.perms = permissions.permission_code
   );

  update sys_menu
     set parent_id = course_menu_id,
         menu_type = 'F',
         visible = '0',
         status = '0',
         icon = '#',
         update_by = 'admin',
         update_time = now()
   where perms in (
     'course:course:query',
     'course:course:add',
     'course:course:edit',
     'course:course:remove',
     'course:module:list',
     'course:module:query',
     'course:module:add',
     'course:module:edit',
     'course:module:remove',
     'course:document:list',
     'course:document:query',
     'course:document:upload',
     'course:document:download',
     'course:document:parse',
     'course:document:remove',
     'course:knowledge-base:query',
     'course:knowledge-base:edit',
     'course:knowledge-base:build',
     'course:knowledge-base:publish',
     'course:member:list',
     'course:member:edit'
   );
end
$$;
