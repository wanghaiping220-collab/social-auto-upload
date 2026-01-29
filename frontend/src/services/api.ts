import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// 账号相关 API
export const accountApi = {
  // 获取账号列表
  getAccounts: (params?: { platform?: string; status?: string }) =>
    api.get('/accounts', { params }),

  // 获取单个账号
  getAccount: (id: number) => api.get(`/accounts/${id}`),

  // 生成登录二维码
  generateQRCode: (platform: string) =>
    api.post('/accounts/qrcode', null, { params: { platform } }),

  // 检查二维码状态
  checkQRCodeStatus: (sessionId: string) =>
    api.get(`/accounts/qrcode/${sessionId}/status`),

  // 刷新二维码
  refreshQRCode: (sessionId: string) =>
    api.post(`/accounts/qrcode/${sessionId}/refresh`),

  // 更新账号
  updateAccount: (id: number, data: { nickname?: string; status?: string }) =>
    api.put(`/accounts/${id}`, data),

  // 删除账号
  deleteAccount: (id: number) => api.delete(`/accounts/${id}`),

  // 检查账号状态
  checkAccountStatus: (id: number) => api.post(`/accounts/${id}/check`),
}

// 内容相关 API
export const contentApi = {
  // 获取内容列表
  getContents: (params?: { skip?: number; limit?: number }) =>
    api.get('/contents', { params }),

  // 获取单个内容
  getContent: (id: number) => api.get(`/contents/${id}`),

  // 上传视频
  uploadVideos: (formData: FormData) =>
    api.post('/contents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5分钟超时
    }),

  // 创建内容
  createContent: (data: {
    title: string
    description?: string
    tags?: string[]
    video_path?: string
    cover_path?: string
  }) => api.post('/contents', data),

  // 更新内容
  updateContent: (
    id: number,
    data: {
      title?: string
      description?: string
      tags?: string[]
      video_path?: string
      cover_path?: string
    }
  ) => api.put(`/contents/${id}`, data),

  // 删除内容
  deleteContent: (id: number) => api.delete(`/contents/${id}`),

  // 批量删除
  batchDelete: (contentIds: number[]) =>
    api.post('/contents/batch/delete', contentIds),

  // 批量更新标题
  batchUpdateTitle: (contentIds: number[], titleTemplate: string) =>
    api.post('/contents/batch/update-title', {
      content_ids: contentIds,
      title_template: titleTemplate,
    }),

  // 批量更新标签
  batchUpdateTags: (contentIds: number[], tags: string[]) =>
    api.post('/contents/batch/update-tags', {
      content_ids: contentIds,
      tags,
    }),

  // 批量更新文案
  batchUpdateDescription: (contentIds: number[], description: string) =>
    api.post('/contents/batch/update-description', {
      content_ids: contentIds,
      description,
    }),
}

// 发布相关 API
export const publishApi = {
  // 获取发布任务列表
  getTasks: (params?: {
    status?: string
    account_id?: number
    content_id?: number
    skip?: number
    limit?: number
  }) => api.get('/publish/tasks', { params }),

  // 获取单个任务
  getTask: (id: number) => api.get(`/publish/tasks/${id}`),

  // 创建发布任务
  createTask: (data: {
    content_id: number
    account_id: number
    scheduled_at?: string
  }) => api.post('/publish/tasks', data),

  // 批量创建发布任务
  batchCreate: (data: {
    content_ids: number[]
    account_ids: number[]
    scheduled_at?: string
  }) => api.post('/publish/batch', data),

  // 执行单个任务
  executeTask: (id: number) => api.post(`/publish/execute/${id}`),

  // 执行所有待发布任务（一键发布）
  executeAll: () => api.post('/publish/execute-all'),

  // 重试失败任务
  retryTask: (id: number) => api.post(`/publish/retry/${id}`),

  // 删除任务
  deleteTask: (id: number) => api.delete(`/publish/tasks/${id}`),

  // 获取统计
  getStats: () => api.get('/publish/stats'),
}

// 日志相关 API
export const logApi = {
  // 获取日志
  getLogs: (params?: {
    level?: string
    module?: string
    start_time?: string
    end_time?: string
    limit?: number
    offset?: number
  }) => api.get('/logs', { params }),

  // 获取最近日志
  getRecentLogs: (params?: { minutes?: number; level?: string }) =>
    api.get('/logs/recent', { params }),

  // 获取日志文件列表
  getLogFiles: () => api.get('/logs/files'),

  // 获取日志统计
  getLogStats: (hours?: number) => api.get('/logs/stats', { params: { hours } }),

  // 清理旧日志
  clearOldLogs: (days: number) =>
    api.delete('/logs/clear', { params: { days } }),
}

export default api
