package com.hezal.common.constant;

/**
 * TrainMind业务常量。
 *
 * @author trainmind
 */
public class TrainMindConstants
{
    /** 默认租户ID */
    public static final Long DEFAULT_TENANT_ID = 1L;

    /** 删除标志：存在 */
    public static final String DEL_FLAG_NORMAL = "0";

    /** 删除标志：删除 */
    public static final String DEL_FLAG_DELETE = "2";

    /** 课程状态：正常 */
    public static final String COURSE_STATUS_ACTIVE = "active";

    /** 课程资料状态：正常 */
    public static final String COURSE_DOCUMENT_STATUS_ACTIVE = "active";

    /** 课程资料状态：归档 */
    public static final String COURSE_DOCUMENT_STATUS_ARCHIVED = "archived";

    /** 资料版本状态：待解析 */
    public static final String DOCUMENT_VERSION_STATUS_UPLOADED = "uploaded";

    /** 资料版本状态：解析中 */
    public static final String DOCUMENT_VERSION_STATUS_PARSING = "parsing";

    /** 资料版本状态：已解析 */
    public static final String DOCUMENT_VERSION_STATUS_PARSED = "parsed";

    /** 资料版本状态：失败 */
    public static final String DOCUMENT_VERSION_STATUS_FAILED = "failed";

    /** 资料版本状态：已归档 */
    public static final String DOCUMENT_VERSION_STATUS_ARCHIVED = "archived";

    /** 解析任务状态：等待中 */
    public static final String PARSE_TASK_STATUS_PENDING = "pending";

    /** 解析任务状态：执行中 */
    public static final String PARSE_TASK_STATUS_RUNNING = "running";

    /** 解析任务状态：成功 */
    public static final String PARSE_TASK_STATUS_SUCCESS = "success";

    /** 解析任务状态：失败 */
    public static final String PARSE_TASK_STATUS_FAILED = "failed";

    /** 解析任务状态：已取消 */
    public static final String PARSE_TASK_STATUS_CANCELLED = "cancelled";

    private TrainMindConstants()
    {
    }
}
