import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Select,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Progress,
  Tooltip,
  Avatar,
} from 'antd'
import {
  SendOutlined,
  ReloadOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { accountApi, contentApi, publishApi } from '../services/api'

interface Account {
  id: number
  platform: string
  nickname: string
  avatar_url: string
  status: string
}

interface Content {
  id: number
  title: string
  description: string
  tags: string[]
}

interface PublishTask {
  id: number
  content_id: number
  account_id: number
  status: string
  error_message: string
  published_url: string
  created_at: string
  published_at: string
  content: Content
  account: Account
}

interface Stats {
  total: number
  pending: number
  uploading: number
  published: number
  failed: number
}

const Publish: React.FC = () => {
  const [tasks, setTasks] = useState<PublishTask[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [contents, setContents] = useState<Content[]>([])
  const [stats, setStats] = useState<Stats>({
    total: 0,
    pending: 0,
    uploading: 0,
    published: 0,
    failed: 0,
  })
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [selectedContents, setSelectedContents] = useState<number[]>([])
  const [selectedAccounts, setSelectedAccounts] = useState<number[]>([])
  const [creating, setCreating] = useState(false)
  const [executing, setExecuting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  // 定时刷新任务状态
  useEffect(() => {
    const interval = setInterval(() => {
      if (stats.uploading > 0) {
        loadTasks()
        loadStats()
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [stats.uploading])

  const loadData = async () => {
    await Promise.all([loadTasks(), loadStats(), loadAccounts(), loadContents()])
  }

  const loadTasks = async () => {
    try {
      setLoading(true)
      const data = await publishApi.getTasks() as PublishTask[]
      setTasks(data)
    } catch (error: unknown) {
      message.error((error as Error).message || '加载任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const data = await publishApi.getStats() as Stats
      setStats(data)
    } catch (error) {
      // ignore
    }
  }

  const loadAccounts = async () => {
    try {
      const data = await accountApi.getAccounts({ status: 'active' }) as Account[]
      setAccounts(data)
    } catch (error) {
      // ignore
    }
  }

  const loadContents = async () => {
    try {
      const data = await contentApi.getContents() as Content[]
      setContents(data)
    } catch (error) {
      // ignore
    }
  }

  const createTasks = async () => {
    if (selectedContents.length === 0) {
      message.warning('请选择要发布的内容')
      return
    }
    if (selectedAccounts.length === 0) {
      message.warning('请选择目标账号')
      return
    }

    try {
      setCreating(true)
      const result = await publishApi.batchCreate({
        content_ids: selectedContents,
        account_ids: selectedAccounts,
      }) as { success: boolean; message: string }

      message.success(result.message)
      setCreateModalVisible(false)
      setSelectedContents([])
      setSelectedAccounts([])
      loadData()
    } catch (error: unknown) {
      message.error((error as Error).message || '创建任务失败')
    } finally {
      setCreating(false)
    }
  }

  const executeAll = async () => {
    try {
      setExecuting(true)
      const result = await publishApi.executeAll() as { success: boolean; message: string }
      message.success(result.message)
      loadData()
    } catch (error: unknown) {
      message.error((error as Error).message || '执行失败')
    } finally {
      setExecuting(false)
    }
  }

  const executeTask = async (id: number) => {
    try {
      await publishApi.executeTask(id)
      message.success('任务已开始执行')
      loadData()
    } catch (error: unknown) {
      message.error((error as Error).message || '执行失败')
    }
  }

  const retryTask = async (id: number) => {
    try {
      await publishApi.retryTask(id)
      message.success('任务已重新加入队列')
      loadData()
    } catch (error: unknown) {
      message.error((error as Error).message || '重试失败')
    }
  }

  const deleteTask = async (id: number) => {
    try {
      await publishApi.deleteTask(id)
      message.success('删除成功')
      loadData()
    } catch (error: unknown) {
      message.error((error as Error).message || '删除失败')
    }
  }

  const getStatusTag = (status: string) => {
    const config: Record<
      string,
      { label: string; color: string; icon: React.ReactNode }
    > = {
      pending: {
        label: '待发布',
        color: 'processing',
        icon: <ClockCircleOutlined />,
      },
      uploading: {
        label: '发布中',
        color: 'purple',
        icon: <SyncOutlined spin />,
      },
      published: {
        label: '已发布',
        color: 'success',
        icon: <CheckCircleOutlined />,
      },
      failed: { label: '失败', color: 'error', icon: <CloseCircleOutlined /> },
    }
    const { label, color, icon } =
      config[status] || { label: status, color: 'default', icon: null }
    return (
      <Tag color={color} icon={icon}>
        {label}
      </Tag>
    )
  }

  const getPlatformTag = (platform: string) => {
    const config: Record<string, { label: string; className: string }> = {
      douyin: { label: '抖音', className: 'platform-tag-douyin' },
      weixin: { label: '视频号', className: 'platform-tag-weixin' },
      xiaohongshu: { label: '小红书', className: 'platform-tag-xiaohongshu' },
    }
    const { label, className } =
      config[platform] || { label: platform, className: '' }
    return <Tag className={className}>{label}</Tag>
  }

  const columns = [
    {
      title: '内容',
      key: 'content',
      width: 250,
      render: (_: unknown, record: PublishTask) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.content?.title || '-'}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            ID: {record.content_id}
          </div>
        </div>
      ),
    },
    {
      title: '目标账号',
      key: 'account',
      width: 200,
      render: (_: unknown, record: PublishTask) => (
        <Space>
          <Avatar src={record.account?.avatar_url} size="small" />
          <div>
            <div>{record.account?.nickname || '-'}</div>
            <div>{getPlatformTag(record.account?.platform)}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: getStatusTag,
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      width: 200,
      ellipsis: true,
      render: (text: string) =>
        text ? (
          <Tooltip title={text}>
            <span style={{ color: '#ff4d4f' }}>{text}</span>
          </Tooltip>
        ) : (
          '-'
        ),
    },
    {
      title: '发布时间',
      dataIndex: 'published_at',
      key: 'published_at',
      width: 180,
      render: (text: string) =>
        text ? new Date(text).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: unknown, record: PublishTask) => (
        <Space>
          {record.status === 'pending' && (
            <Tooltip title="立即执行">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={() => executeTask(record.id)}
              />
            </Tooltip>
          )}
          {record.status === 'failed' && (
            <Tooltip title="重试">
              <Button
                type="text"
                icon={<ReloadOutlined />}
                onClick={() => retryTask(record.id)}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="确定删除此任务？"
            onConfirm={() => deleteTask(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const progressPercent =
    stats.total > 0
      ? Math.round(((stats.published + stats.failed) / stats.total) * 100)
      : 0

  return (
    <div className="fade-in">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="待发布"
              value={stats.pending}
              prefix={<ClockCircleOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="发布中"
              value={stats.uploading}
              prefix={<SyncOutlined spin style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="已发布"
              value={stats.published}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="发布失败"
              value={stats.failed}
              prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
            />
          </Card>
        </Col>
      </Row>

      {stats.total > 0 && (
        <Card style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span>发布进度：</span>
            <Progress
              percent={progressPercent}
              status={stats.failed > 0 ? 'exception' : 'active'}
              style={{ flex: 1 }}
            />
            <span>
              {stats.published + stats.failed} / {stats.total}
            </span>
          </div>
        </Card>
      )}

      <Card
        title="发布任务"
        style={{ marginTop: 16 }}
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadData}>
              刷新
            </Button>
            <Button
              icon={<SendOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建任务
            </Button>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              onClick={executeAll}
              loading={executing}
              disabled={stats.pending === 0}
            >
              一键发布
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: total => `共 ${total} 个任务`,
          }}
        />
      </Card>

      {/* 创建任务弹窗 */}
      <Modal
        title="创建发布任务"
        open={createModalVisible}
        onOk={createTasks}
        onCancel={() => {
          setCreateModalVisible(false)
          setSelectedContents([])
          setSelectedAccounts([])
        }}
        okText="创建"
        cancelText="取消"
        confirmLoading={creating}
        width={700}
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>选择内容：</div>
          <Select
            mode="multiple"
            style={{ width: '100%' }}
            placeholder="选择要发布的内容"
            value={selectedContents}
            onChange={setSelectedContents}
            options={contents.map(c => ({
              value: c.id,
              label: c.title,
            }))}
            optionFilterProp="label"
            showSearch
            maxTagCount={5}
          />
        </div>

        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>选择目标账号：</div>
          <Select
            mode="multiple"
            style={{ width: '100%' }}
            placeholder="选择目标账号"
            value={selectedAccounts}
            onChange={setSelectedAccounts}
            optionFilterProp="label"
            showSearch
            maxTagCount={5}
          >
            {accounts.map(account => (
              <Select.Option key={account.id} value={account.id}>
                <Space>
                  <Avatar src={account.avatar_url} size="small" />
                  <span>{account.nickname}</span>
                  {getPlatformTag(account.platform)}
                </Space>
              </Select.Option>
            ))}
          </Select>
        </div>

        {selectedContents.length > 0 && selectedAccounts.length > 0 && (
          <div
            style={{
              marginTop: 16,
              padding: 12,
              background: '#f5f5f5',
              borderRadius: 6,
            }}
          >
            将创建 <strong>{selectedContents.length * selectedAccounts.length}</strong> 个发布任务
            （{selectedContents.length} 个内容 × {selectedAccounts.length} 个账号）
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Publish
