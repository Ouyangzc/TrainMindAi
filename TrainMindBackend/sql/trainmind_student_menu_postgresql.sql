-- TrainMind 学员端菜单与路由（PostgreSQL）
-- 学员端页面必须走 sys_menu，由菜单管理和角色授权控制，不在前端硬编码路由。
-- 本脚本可重复执行，并自动向 student 角色授权学员端菜单。

\ir trainmind_student_role_postgresql.sql

select setval(
  pg_get_serial_sequence('sys_menu', 'menu_id'),
  greatest(coalesce((select max(menu_id) from sys_menu), 1), 1),
  true
);

do $$
declare
  student_root_id int8;
  courses_menu_id int8;
  course_space_id int8;
  student_role_id int8;
begin
  select menu_id
    into student_root_id
    from sys_menu
   where parent_id = 0 and path = 'student' and menu_type = 'M'
   order by menu_id
   limit 1;

  if student_root_id is null then
    insert into sys_menu(
      menu_name, parent_id, order_num, path, component, "query", route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) values (
      '学员学习', 0, 5, 'student', '', null, 'Student',
      1, 0, 'M', '0', '0', '', 'education',
      'admin', now(), '', null, '学员端菜单目录'
    )
    returning menu_id into student_root_id;
  else
    update sys_menu
       set menu_name = '学员学习',
           parent_id = 0,
           order_num = 5,
           path = 'student',
           component = '',
           route_name = 'Student',
           is_frame = 1,
           is_cache = 0,
           menu_type = 'M',
           visible = '0',
           status = '0',
           perms = '',
           icon = 'education',
           update_by = 'admin',
           update_time = now(),
           remark = '学员端菜单目录'
     where menu_id = student_root_id;
  end if;

  select menu_id
    into courses_menu_id
    from sys_menu
   where parent_id = student_root_id and (path = 'courses' or route_name = 'StudentCourses')
   order by menu_id
   limit 1;

  if courses_menu_id is null then
    insert into sys_menu(
      menu_name, parent_id, order_num, path, component, "query", route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) values (
      '我的课程', student_root_id, 1, 'courses', 'student/courses/index', null, 'StudentCourses',
      1, 0, 'C', '0', '0', 'student:course:list', 'education',
      'admin', now(), '', null, '学员端课程列表'
    )
    returning menu_id into courses_menu_id;
  else
    update sys_menu
       set menu_name = '我的课程',
           parent_id = student_root_id,
           order_num = 1,
           path = 'courses',
           component = 'student/courses/index',
           route_name = 'StudentCourses',
           is_frame = 1,
           is_cache = 0,
           menu_type = 'C',
           visible = '0',
           status = '0',
           perms = 'student:course:list',
           icon = 'education',
           update_by = 'admin',
           update_time = now(),
           remark = '学员端课程列表'
     where menu_id = courses_menu_id;
  end if;

  select menu_id
    into course_space_id
    from sys_menu
   where parent_id = student_root_id
     and (path = E'courses/:courseId(\\d+)' or route_name = 'StudentCourseSpace')
   order by menu_id
   limit 1;

  if course_space_id is null then
    insert into sys_menu(
      menu_name, parent_id, order_num, path, component, "query", route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) values (
      '课程空间', student_root_id, 2, E'courses/:courseId(\\d+)', 'student/course-space/index', null, 'StudentCourseSpace',
      1, 0, 'M', '1', '0', 'student:course:query', 'education',
      'admin', now(), '', null, '学员端课程空间隐藏路由'
    )
    returning menu_id into course_space_id;
  else
    update sys_menu
       set menu_name = '课程空间',
           parent_id = student_root_id,
           order_num = 2,
           path = E'courses/:courseId(\\d+)',
           component = 'student/course-space/index',
           route_name = 'StudentCourseSpace',
           is_frame = 1,
           is_cache = 0,
           menu_type = 'M',
           visible = '1',
           status = '0',
           perms = 'student:course:query',
           icon = 'education',
           update_by = 'admin',
           update_time = now(),
           remark = '学员端课程空间隐藏路由'
     where menu_id = course_space_id;
  end if;

  insert into sys_menu(
    menu_name, parent_id, order_num, path, component, "query", route_name,
    is_frame, is_cache, menu_type, visible, status, perms, icon,
    create_by, create_time, update_by, update_time, remark
  )
  select menu_name, course_space_id, order_num, path, component, null, route_name,
         1, 0, 'C', '1', '0', perms, '#',
         'admin', now(), '', null, remark
    from (values
      ('AI 学习助教', 1, 'assistant', 'student/course-space/assistant', 'StudentCourseAssistant', 'student:course:chat', '学员端 AI 学习助教隐藏路由'),
      ('课程目录', 2, 'outline', 'student/course-space/outline', 'StudentCourseOutline', 'student:course:outline', '学员端课程目录隐藏路由'),
      ('资料库', 3, 'library', 'student/course-space/library', 'StudentCourseLibrary', 'student:course:document:list', '学员端资料库隐藏路由'),
      ('学习记录', 4, 'activities', 'student/course-space/activities', 'StudentCourseActivities', 'student:course:activity:list', '学员端学习记录隐藏路由'),
      ('资料预览', 5, E'documents/:documentId(\\d+)/preview', 'student/course-space/document-preview', 'StudentDocumentPreview', 'student:course:document:preview', '学员端资料预览隐藏路由')
    ) as route_menus(menu_name, order_num, path, component, route_name, perms, remark)
   where not exists (
     select 1
       from sys_menu existing
      where existing.parent_id = course_space_id
        and (existing.path = route_menus.path or existing.route_name = route_menus.route_name)
   );

  update sys_menu existing
     set menu_name = route_menus.menu_name,
         parent_id = course_space_id,
         order_num = route_menus.order_num,
         path = route_menus.path,
         component = route_menus.component,
         route_name = route_menus.route_name,
         is_frame = 1,
         is_cache = 0,
         menu_type = 'C',
         visible = '1',
         status = '0',
         perms = route_menus.perms,
         icon = '#',
         update_by = 'admin',
         update_time = now(),
         remark = route_menus.remark
    from (values
      ('AI 学习助教', 1, 'assistant', 'student/course-space/assistant', 'StudentCourseAssistant', 'student:course:chat', '学员端 AI 学习助教隐藏路由'),
      ('课程目录', 2, 'outline', 'student/course-space/outline', 'StudentCourseOutline', 'student:course:outline', '学员端课程目录隐藏路由'),
      ('资料库', 3, 'library', 'student/course-space/library', 'StudentCourseLibrary', 'student:course:document:list', '学员端资料库隐藏路由'),
      ('学习记录', 4, 'activities', 'student/course-space/activities', 'StudentCourseActivities', 'student:course:activity:list', '学员端学习记录隐藏路由'),
      ('资料预览', 5, E'documents/:documentId(\\d+)/preview', 'student/course-space/document-preview', 'StudentDocumentPreview', 'student:course:document:preview', '学员端资料预览隐藏路由')
    ) as route_menus(menu_name, order_num, path, component, route_name, perms, remark)
   where existing.parent_id = course_space_id
     and (existing.path = route_menus.path or existing.route_name = route_menus.route_name);

  select role_id
    into student_role_id
    from sys_role
   where role_key = 'student' and del_flag = '0'
   order by role_id
   limit 1;

  if student_role_id is not null then
    insert into sys_role_menu(role_id, menu_id)
    select student_role_id, m.menu_id
      from sys_menu m
     where (m.menu_id in (student_root_id, courses_menu_id, course_space_id)
        or m.parent_id = course_space_id)
       and not exists (
         select 1
           from sys_role_menu rm
          where rm.role_id = student_role_id
            and rm.menu_id = m.menu_id
       );
  end if;
end
$$;
