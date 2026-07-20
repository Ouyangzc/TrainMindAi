package com.hezal.system.service;

import java.util.List;
import com.hezal.system.domain.CourseUser;

/** 课程成员直接授权服务。 */
public interface ICourseUserService
{
    List<CourseUser> selectMembers(Long courseId);
    CourseUser addMember(Long courseId, CourseUser member, String username);
    CourseUser updateMember(Long courseId, Long memberId, CourseUser member, String username);
    int deleteMember(Long courseId, Long memberId, String username);
    CourseUser transferOwner(Long courseId, Long targetUserId, String username);
}
